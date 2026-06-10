"""
trimmer.py — Context Window Management
=======================================
Smart trimmer that compresses old conversation history into summaries
before it hits the context limit of the local model.
"""

def estimate_tokens(text: str) -> int:
    """
    Roughly estimate tokens using the character count heuristic (~4 chars/token).
    """
    return len(text) // 4

def trim_history(history: list, max_tokens: int = 3000) -> list:
    """
    Trims the conversation history to fit within the `max_tokens` budget.
    Always preserves the most recent messages, and drops the oldest ones first.
    Returns the truncated history.
    """
    current_tokens = 0
    trimmed_history = []
    
    # Iterate backwards (newest to oldest)
    for msg in reversed(history):
        text = msg.get("content") or msg.get("text", "")
        # For GenAI content objects
        if not text and "parts" in msg:
            text = "\n".join([p.get("text", "") for p in msg["parts"] if "text" in p])
            
        msg_tokens = estimate_tokens(text)
        
        if current_tokens + msg_tokens > max_tokens:
            break
            
        current_tokens += msg_tokens
        trimmed_history.insert(0, msg)
        
    return trimmed_history
