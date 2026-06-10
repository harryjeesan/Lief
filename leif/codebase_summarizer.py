import httpx
from tqdm import tqdm
import logging
import json
import os

logging.basicConfig(level=logging.INFO)

OLLAMA_URL = "http://localhost:11434/api/generate"
SUMMARIZER_MODEL = "qwen2.5-coder:1.5b"

SYSTEM_PROMPT = """You are an expert software architect.
I will give you a block of code (a function, class, or chunk).
Your job is to summarize what this code does in EXACTLY 1 OR 2 SENTENCES.
Do not explain the syntax. Do not write code. Just explain the high-level business logic or purpose.
Keep it extremely concise."""

def summarize_code_blocks(blocks):
    summaries = []
    
    # Check if Ollama is running
    try:
        httpx.get("http://localhost:11434/")
    except httpx.ConnectError:
        logging.error("Ollama is not running. Please start Ollama.")
        return []

    print(f"\nGenerating summaries for {len(blocks)} code blocks...")
    
    # We use httpx.Client to keep the connection open for speed
    with httpx.Client(timeout=30.0) as client:
        for block in tqdm(blocks, desc="Summarizing", unit="block"):
            prompt = f"File: {block['file']}\nType: {block['type']}\nName: {block['name']}\nCode:\n{block['code']}\n\nSummary:"
            
            try:
                response = client.post(OLLAMA_URL, json={
                    "model": SUMMARIZER_MODEL,
                    "system": SYSTEM_PROMPT,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Keep it deterministic
                        "num_ctx": 2048
                    }
                })
                
                if response.status_code == 200:
                    summary_text = response.json().get("response", "").strip()
                else:
                    summary_text = f"Error: Ollama returned {response.status_code}"
                    
            except Exception as e:
                summary_text = f"Error summarizing: {str(e)}"
                
            summaries.append({
                "file": block['file'],
                "name": block['name'],
                "type": block['type'],
                "summary": summary_text
            })
            
    return summaries

if __name__ == "__main__":
    # Quick test if reader_test_output.json exists
    if os.path.exists("reader_test_output.json"):
        with open("reader_test_output.json", "r") as f:
            test_blocks = json.load(f)
            
        print(f"Loaded {len(test_blocks)} blocks for testing.")
        
        # Test on just the first 3 blocks to save time
        test_summaries = summarize_code_blocks(test_blocks[:3])
        
        with open("summarizer_test_output.json", "w") as f:
            json.dump(test_summaries, f, indent=2)
            
        print("\nTest complete! Check summarizer_test_output.json")
    else:
        print("Run codebase_reader.py first to generate test data.")
