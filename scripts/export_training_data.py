import sqlite3
import json
import logging
import os

logging.basicConfig(level=logging.INFO)

DB_PATH = r'D:\Leif_Data\leif_memory.db'
OUTPUT_FILE = r'scripts\training_data.jsonl'

def export_data():
    if not os.path.exists(DB_PATH):
        logging.error(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get all conversation IDs
    c.execute('SELECT id FROM conversations')
    conversations = c.fetchall()
    
    total_convos = 0
    total_messages = 0

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for (conv_id,) in conversations:
            # Fetch all messages for this conversation ordered by time
            c.execute('SELECT sender, content FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC', (conv_id,))
            messages = c.fetchall()

            if not messages:
                continue

            # Format for Unsloth / Llama-3 / ChatML
            formatted_messages = []
            for sender, content in messages:
                # Map internal roles to standard training roles
                role = "assistant" if sender == "model" else "user"
                formatted_messages.append({
                    "role": role,
                    "content": content
                })

            # Create the JSONL object
            jsonl_obj = {
                "conversations": formatted_messages
            }

            # Write as a single line JSON
            f.write(json.dumps(jsonl_obj, ensure_ascii=False) + '\n')
            
            total_convos += 1
            total_messages += len(messages)

    conn.close()
    
    logging.info(f"✅ Export complete!")
    logging.info(f"Saved to: {OUTPUT_FILE}")
    logging.info(f"Total Conversations Exported: {total_convos}")
    logging.info(f"Total Message Pairs: {total_messages}")

if __name__ == '__main__':
    export_data()
