import os
from fastapi import APIRouter, HTTPException
from leif.database import (
    list_conversations, create_conversation,
    delete_conversation, get_history, get_metrics
)
from leif.local_llm import get_ollama_status
from leif.llm_router import get_router_status

router = APIRouter()

@router.get("/api/local-status")
async def get_local_status():
    ollama_enabled = os.getenv("LOCAL_LLM_ENABLED", "true").lower() == "true"
    ollama_model   = os.getenv("OLLAMA_MODEL", "phi3:mini")
    status = get_ollama_status()
    return {
        "enabled": ollama_enabled,
        "online":  status["online"],
        "model":   ollama_model,
        "available_models": status["models"],
    }

@router.get("/api/metrics")
async def get_metrics_endpoint():
    return get_metrics()

@router.get("/api/key-status")
async def get_key_status():
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    next_reset_utc = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now >= next_reset_utc:
        next_reset_utc += timedelta(days=1)

    seconds_until_reset = int((next_reset_utc - now).total_seconds())
    hours, rem = divmod(seconds_until_reset, 3600)
    minutes = rem // 60

    status = get_router_status()
    api_keys = status["API_KEYS"]
    current_idx = status["current_key_index"]
    exhausted_at_dict = status["key_exhausted_at"]

    keys_status = []
    for i, key in enumerate(api_keys):
        exhausted_at = exhausted_at_dict.get(i)
        is_active = (i == current_idx)
        is_exhausted = i in exhausted_at_dict

        keys_status.append({
            "index": i + 1,
            "key_hint": f"...{key[-6:]}",
            "status": "active" if is_active and not is_exhausted else "exhausted" if is_exhausted else "standby",
            "exhausted_at": exhausted_at,
            "resets_in": f"{hours}h {minutes}m" if is_exhausted else None,
        })

    return {
        "total_keys": len(api_keys),
        "active_key": current_idx + 1,
        "primary_model": status["primary_model"],
        "fallback_model": status["fallback_model"],
        "next_reset_utc": next_reset_utc.isoformat(),
        "keys": keys_status,
        "groq_model": status.get("groq_model"),
        "has_groq_fallback": status.get("has_groq_fallback", False)
    }

@router.get("/api/conversations")
async def get_conversations():
    return {"conversations": list_conversations()}

@router.post("/api/conversations")
async def new_conversation():
    conv_id = create_conversation()
    return {"id": conv_id, "title": "New Chat"}

@router.delete("/api/conversations/{conv_id}")
async def remove_conversation(conv_id: str):
    try:
        delete_conversation(conv_id)
        return {"ok": True}
    except Exception as e:
        print(f"Error deleting conversation {conv_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/conversations/{conv_id}/messages")
async def get_conversation_messages(conv_id: str):
    _, react_history = get_history(conversation_id=conv_id)
    return {"history": react_history}
