import json
import sqlite3
import uuid
import os

# Ensure this points to your actual database location!
DB_PATH = r"D:\Leif_Data\leif_memory.db"
JSON_DATA_PATH = os.path.join(os.path.dirname(__file__), "synthetic_data.json")

def inject_synthetic_data():
    if not os.path.exists(JSON_DATA_PATH):
        print(f"Error: Could not find {JSON_DATA_PATH}")
        return

    with open(JSON_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    success_count = 0

    for item in data:
        title = item.get("title", "Synthetic Chat")
        prompt = item.get("prompt")
        response = item.get("perfect_response")
        
        if not prompt or not response:
            print(f"Warning: Skipping incomplete item: {title}")
            continue

        # 1. Create a new conversation
        conv_id = str(uuid.uuid4())
        c.execute("INSERT INTO conversations (id, title) VALUES (?, ?)", (conv_id, title))
        
        # 2. Insert User Prompt
        c.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (?, ?, ?)", 
                  (conv_id, "user", prompt))
        
        # 3. Insert Perfect AI Response
        c.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (?, ?, ?)", 
                  (conv_id, "model", response))
        
        success_count += 1
        print(f"Success - Injected: {title}")

    conn.commit()
    conn.close()
    
    print(f"\nSuccessfully injected {success_count} perfect conversations into leif_memory.db!")

if __name__ == "__main__":
    inject_synthetic_data()
