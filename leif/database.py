import sqlite3
import os
import uuid
import time
from datetime import datetime

try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

# Create a dedicated data folder on the D: drive to save space on C:
DATA_DIR = r"D:\Leif_Data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_PATH = os.path.join(DATA_DIR, 'leif_memory.db')

# Initialize ChromaDB persistent client for Vector Memories
if HAS_CHROMA:
    chroma_client = chromadb.PersistentClient(path=os.path.join(DATA_DIR, 'chroma'))
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Get or create the memory collection
    memory_collection = chroma_client.get_or_create_collection(
        name="leif_long_term_memory",
        embedding_function=sentence_transformer_ef
    )
else:
    memory_collection = None

def init_db():
    """Create the database tables if they don't exist. Migrates old schema automatically."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Conversations table — one row per chat session
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT 'New Chat',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Messages table — scoped to a conversation
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    ''')

    # Metrics table — tracking token usage globally
    c.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY DEFAULT 1,
            local_requests INTEGER DEFAULT 0,
            cloud_requests INTEGER DEFAULT 0,
            local_tokens INTEGER DEFAULT 0,
            cloud_tokens INTEGER DEFAULT 0,
            estimated_savings REAL DEFAULT 0.0
        )
    ''')
    
    # Initialize the single row if it doesn't exist
    c.execute("INSERT OR IGNORE INTO metrics (id) VALUES (1)")

    # Migration: if old messages table exists without conversation_id, migrate them
    c.execute("PRAGMA table_info(messages)")
    columns = [row[1] for row in c.fetchall()]
    if 'conversation_id' not in columns:
        # Create a legacy conversation to hold old messages
        legacy_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO conversations (id, title) VALUES (?, ?)",
            (legacy_id, "Legacy Conversation")
        )
        c.execute("ALTER TABLE messages ADD COLUMN conversation_id TEXT")
        c.execute("UPDATE messages SET conversation_id = ?", (legacy_id,))

    conn.commit()
    conn.close()

# ============================================================
# CONVERSATION MANAGEMENT
# ============================================================

def create_conversation(title="New Chat") -> str:
    """Create a new conversation and return its ID."""
    conv_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO conversations (id, title) VALUES (?, ?)",
        (conv_id, title)
    )
    conn.commit()
    conn.close()
    return conv_id

def list_conversations() -> list:
    """Return all conversations ordered by most recent activity."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT c.id, c.title, c.created_at, c.updated_at,
               COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        GROUP BY c.id
        ORDER BY c.updated_at DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
            "message_count": row[4]
        }
        for row in rows
    ]

def rename_conversation(conv_id: str, title: str):
    """Update the title of a conversation."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id))
    conn.commit()
    conn.close()

def delete_conversation(conv_id: str):
    """Delete a conversation and all its messages."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    c.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()

# ============================================================
# MESSAGE MANAGEMENT
# ============================================================

def save_message(sender: str, content: str, conversation_id: str = None):
    """Save a message. If no conversation_id, saves to the most recent conversation."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if not conversation_id:
        # Fallback: use most recent conversation
        c.execute("SELECT id FROM conversations ORDER BY updated_at DESC LIMIT 1")
        row = c.fetchone()
        conversation_id = row[0] if row else create_conversation()

    c.execute(
        'INSERT INTO messages (conversation_id, sender, content) VALUES (?, ?, ?)',
        (conversation_id, sender, content)
    )
    # Auto-generate a title from the first user message
    if sender == "user":
        c.execute(
            "SELECT title FROM conversations WHERE id = ?", (conversation_id,)
        )
        row = c.fetchone()
        if row and row[0] == "New Chat":
            title = content[:50].strip()
            if len(content) > 50:
                title += "..."
            c.execute(
                "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, conversation_id)
            )
        else:
            c.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )

    conn.commit()
    conn.close()

def get_history(conversation_id: str = None):
    """Retrieve message history for a conversation."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if conversation_id:
        c.execute(
            'SELECT id, sender, content FROM messages WHERE conversation_id = ? ORDER BY id ASC',
            (conversation_id,)
        )
    else:
        # Fallback: most recent conversation
        c.execute('''
            SELECT m.id, m.sender, m.content
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            ORDER BY c.updated_at DESC, m.id ASC
            LIMIT 100
        ''')

    rows = c.fetchall()
    conn.close()

    react_history = []
    gemini_history = []

    for row in rows:
        msg_id, sender, content = row
        react_history.append({"id": msg_id, "sender": sender, "text": content})
        role = "user" if sender == "user" else "model"
        gemini_history.append({"role": role, "parts": [{"text": content}]})

    return gemini_history, react_history

# ============================================================
# VECTOR MEMORY (LONG-TERM)
# ============================================================

def save_long_term_memory(topic: str, summary: str, code_snippets: str = ""):
    """Save a dense summary to the ChromaDB vector database."""
    if not HAS_CHROMA or not memory_collection:
        print("ChromaDB not installed or unavailable.")
        return False
        
    try:
        mem_id = str(uuid.uuid4())
        content = f"Topic: {topic}\nSummary: {summary}\nCode context: {code_snippets}"
        
        memory_collection.add(
            documents=[content],
            metadatas=[{"topic": topic, "timestamp": str(time.time())}],
            ids=[mem_id]
        )
        print(f"✅ Memory saved to ChromaDB: {topic}")
        return True
    except Exception as e:
        print(f"Error saving vector memory: {e}")
        return False

def search_memories(query: str, limit: int = 3) -> str:
    """Search ChromaDB for relevant memories."""
    if not HAS_CHROMA or not memory_collection:
        return ""
        
    try:
        results = memory_collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        if not results['documents'] or not results['documents'][0]:
            return ""
            
        memories = results['documents'][0]
        if memories:
            return "\n\n---\n[CORE MEMORIES RETRIEVED FROM PAST PROJECTS]\n" + "\n\n".join(memories) + "\n---\n"
        return ""
    except Exception as e:
        print(f"Error searching vector memory: {e}")
        return ""

# ============================================================
# METRICS TRACKING
# ============================================================

def update_metrics(is_local: bool, tokens: int, cost_savings: float = 0.0):
    """Update global token and request metrics."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if is_local:
        c.execute('''
            UPDATE metrics 
            SET local_requests = local_requests + 1,
                local_tokens = local_tokens + ?,
                estimated_savings = estimated_savings + ?
            WHERE id = 1
        ''', (tokens, cost_savings))
    else:
        c.execute('''
            UPDATE metrics 
            SET cloud_requests = cloud_requests + 1,
                cloud_tokens = cloud_tokens + ?
            WHERE id = 1
        ''', (tokens,))
    conn.commit()
    conn.close()

def get_metrics() -> dict:
    """Retrieve current metrics."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT local_requests, cloud_requests, local_tokens, cloud_tokens, estimated_savings FROM metrics WHERE id = 1')
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "local_requests": row[0],
            "cloud_requests": row[1],
            "local_tokens": row[2],
            "cloud_tokens": row[3],
            "estimated_savings": row[4]
        }
    return {
        "local_requests": 0,
        "cloud_requests": 0,
        "local_tokens": 0,
        "cloud_tokens": 0,
        "estimated_savings": 0.0
    }
