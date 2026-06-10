import os
from datetime import datetime, timezone
from google import genai
from google.genai import types
from groq import Groq
from dotenv import load_dotenv
from leif.system_prompt import LEIF_SYSTEM_PROMPT
from leif.database import update_metrics

load_dotenv()

# ============================================================
# KEY ROTATION POOL
# ============================================================
_raw_keys = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
]
API_KEYS = [k for k in _raw_keys if k and k.strip()]

if not API_KEYS:
    raise RuntimeError("❌ No valid GEMINI_API_KEY found. Check your .env file.")

# Start with the first key
_current_key_index = 0
client = genai.Client(api_key=API_KEYS[_current_key_index])

# The Models
PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.5-flash-lite"

# Groq — Ultimate fallback
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Tracks when each key was marked exhausted (index -> ISO timestamp)
_key_exhausted_at = {}

def get_router_status():
    """Returns the internal state of the router for the /api/key-status endpoint."""
    return {
        "API_KEYS": API_KEYS,
        "current_key_index": _current_key_index,
        "key_exhausted_at": _key_exhausted_at,
        "primary_model": PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "groq_model": GROQ_MODEL,
        "has_groq_fallback": bool(groq_client)
    }

def _rotate_key(exhausted_index):
    """Record exhaustion timestamp and switch to the next available API key."""
    global _current_key_index, client
    _key_exhausted_at[exhausted_index] = datetime.now(timezone.utc).isoformat()
    _current_key_index = (_current_key_index + 1) % len(API_KEYS)
    client = genai.Client(api_key=API_KEYS[_current_key_index])
    print(f"Rotated to API Key #{_current_key_index + 1}")

def _groq_generate(contents, is_json_mode=False):
    """
    Calls Groq's Llama 3.3 70B
    """
    ROLE_MAP = {"user": "user", "assistant": "assistant", "model": "assistant", "leif": "assistant"}
    
    messages = []
    if isinstance(contents, list):
        for c in contents:
            # Handle dictionary formats
            if isinstance(c, dict):
                role = ROLE_MAP.get(c.get("role"), "user")
                text = ""
                parts = c.get("parts", [])
                if parts and isinstance(parts[0], dict):
                    text = parts[0].get("text", "")
                messages.append({"role": role, "content": text})
            # Handle genai.types.Content format
            else:
                role = ROLE_MAP.get(c.role, "user")
                text_parts = []
                if c.parts:
                    for part in c.parts:
                        if hasattr(part, "text") and part.text:
                            text_parts.append(part.text)
                text = "\n".join(text_parts)
                if text:
                    messages.append({"role": role, "content": text})
    elif isinstance(contents, str):
        messages = [{"role": "user", "content": contents}]

    # Truncate to last 8 messages
    if len(messages) > 8:
        messages = messages[-8:]

    kwargs = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": LEIF_SYSTEM_PROMPT}] + messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    
    if is_json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    chat = groq_client.chat.completions.create(**kwargs)
    
    # Track Groq token usage
    tokens = chat.usage.total_tokens if hasattr(chat, 'usage') and chat.usage else 0
    update_metrics(is_local=False, tokens=tokens)
    
    class _GroqResponse:
        def __init__(self, text): self.text = text
    return _GroqResponse(chat.choices[0].message.content)

def generate_with_fallback(contents, config=None, is_json_mode=False):
    """
    3-TIER INTELLIGENCE ROUTER
    """
    global _current_key_index
    
    # Fast path: if all Gemini keys are exhausted, skip Gemini entirely
    if len(_key_exhausted_at) >= len(API_KEYS):
        if groq_client:
            print(f"All Gemini keys are marked exhausted. Instantly routing to Groq {GROQ_MODEL}...")
            try:
                return _groq_generate(contents, is_json_mode=is_json_mode)
            except Exception as e:
                raise RuntimeError(f"All Gemini keys exhausted AND Groq fallback failed: {e}")
        else:
            raise RuntimeError("All Gemini keys exhausted and Groq fallback is not configured.")

    # Tier 1: Gemini 2.5 Flash
    for attempt in range(len(API_KEYS)):
        if _current_key_index in _key_exhausted_at:
            _rotate_key(_current_key_index)
            continue
            
        try:
            res = client.models.generate_content(
                model=PRIMARY_MODEL,
                contents=contents,
                config=config
            )
            tokens = res.usage_metadata.total_token_count if hasattr(res, 'usage_metadata') and res.usage_metadata else 0
            update_metrics(is_local=False, tokens=tokens)
            return res
        except Exception as e:
            err_str = str(e).lower()
            if any(code in err_str for code in ['429', '503', '500', '502', '504', 'quota']):
                exhausted_idx = _current_key_index
                print(f"Gemini API error ({e}). Rotating key...")
                _rotate_key(exhausted_idx)
            else:
                print(f"Gemini API critical error ({e}). Bypassing rotation...")
                break # Break to fallback to Tier 2

    # Tier 2: Gemini 2.5 Flash Lite
    # Only try Lite if we haven't exhausted all keys during Tier 1
    if len(_key_exhausted_at) < len(API_KEYS):
        for attempt in range(len(API_KEYS)):
            if _current_key_index in _key_exhausted_at:
                _rotate_key(_current_key_index)
                continue
                
            try:
                print(f"Trying {FALLBACK_MODEL}...")
                res = client.models.generate_content(
                    model=FALLBACK_MODEL, 
                    contents=contents, 
                    config=config
                )
                tokens = res.usage_metadata.total_token_count if hasattr(res, 'usage_metadata') and res.usage_metadata else 0
                update_metrics(is_local=False, tokens=tokens)
                return res
            except Exception as e:
                err_str = str(e).lower()
                if any(code in err_str for code in ['429', '503', '500', '502', '504', 'quota']):
                    _rotate_key(_current_key_index)
                else:
                    break # Break to fallback to Tier 3

    # Tier 3: Groq ultimate fallback
    if groq_client:
        print(f"All Gemini keys exhausted/unavailable. Routing to Groq {GROQ_MODEL}...")
        try:
            return _groq_generate(contents, is_json_mode=is_json_mode)
        except Exception as e:
            raise RuntimeError(f"Groq Fallback also failed: {e}")
    
    raise RuntimeError("All tiers exhausted and Groq fallback is not configured.")
