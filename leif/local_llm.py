"""
local_llm.py — Leif's Tier 0 Local Brain
==========================================
Wraps the Ollama HTTP API to provide free, offline inference
using Phi-3 Mini (or any locally installed GGUF model).

Returns a structured result with an 'escalate' flag so the main
router knows whether to pass the task up to Gemini (Tier 1).
"""

import httpx

# ── Configuration ──────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
GENERATE_URL    = f"{OLLAMA_BASE_URL}/api/generate"
CHAT_URL        = f"{OLLAMA_BASE_URL}/api/chat"
HEALTH_URL      = f"{OLLAMA_BASE_URL}/api/tags"

# Phrases that indicate the local model is uncertain or out of its depth.
# If any of these appear in the response, we escalate to Gemini.
ESCALATION_PHRASES = [
    "i don't know",
    "i'm not sure",
    "i cannot",
    "i'm unable",
    "i don't have access",
    "as a language model",
    "beyond my capabilities",
    "i lack the ability",
    "i have no information",
    "i cannot provide",
]


# ── Health Check ───────────────────────────────────────────────────────────────
def is_ollama_running() -> bool:
    """Returns True if the Ollama server is reachable on localhost:11434."""
    try:
        response = httpx.get(HEALTH_URL, timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def get_ollama_status() -> dict:
    """
    Returns a status dict for the /api/local-status endpoint.
    Includes whether Ollama is online and which models are available.
    """
    try:
        response = httpx.get(HEALTH_URL, timeout=3)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            return {
                "online": True,
                "models": models,
            }
    except Exception:
        return {"online": False, "models": []}


def prewarm_local_model(model: str = "phi3:mini"):
    """
    Sends an empty prompt to Ollama to force it to load the model into VRAM
    so that the first actual user request is instantaneous.
    """
    import threading
    def _warm():
        try:
            httpx.post(
                CHAT_URL,
                json={"model": model, "messages": [{"role": "user", "content": "hello"}], "stream": False},
                timeout=30
            )
        except Exception:
            pass
    threading.Thread(target=_warm, daemon=True).start()


# ── Core Inference ─────────────────────────────────────────────────────────────
def query_local(
    prompt: str,
    model: str = "phi3:mini",
    system_prompt: str = "",
    timeout: int = 30,
) -> dict:
    """
    Sends a prompt to the local Ollama model and returns a structured result.

    Returns:
        {
            "text":     str   — the model's response text,
            "escalate": bool  — True if Leif should pass this to Gemini,
            "reason":   str   — why escalation was triggered (for logging),
        }
    """
    if not is_ollama_running():
        return {
            "text": "",
            "escalate": True,
            "reason": "ollama_offline",
        }

    try:
        from leif.database import update_metrics
        
        # Use the /api/chat endpoint for a cleaner message-based interface
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            CHAT_URL,
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_ctx": 4096,
                },
            },
            timeout=timeout,
        )

        data = response.json()
        text = data.get("message", {}).get("content", "").strip()
        tokens = data.get("prompt_eval_count", 0) + data.get("eval_count", 0)

        # ── Escalation Detection ──────────────────────────────────────────────
        # 1. Response is too short to be useful
        if len(text) < 20:
            return {"text": text, "escalate": True, "reason": "response_too_short"}

        # 2. Model signals uncertainty
        text_lower = text.lower()
        for phrase in ESCALATION_PHRASES:
            if phrase in text_lower:
                return {"text": text, "escalate": True, "reason": f"uncertainty: '{phrase}'"}

        # 3. Unclosed code block — model got confused mid-generation
        if text.count("```") % 2 != 0:
            return {"text": text, "escalate": True, "reason": "unclosed_code_block"}

        # All checks passed — local model handled it
        # Calculate cost savings (Assuming Gemini 1.5 Pro pricing: $1.25 / 1M input + $5.00 / 1M output)
        # For simplicity, we blend it as ~$3.00 / 1M tokens.
        savings = (tokens / 1000000) * 3.00
        update_metrics(is_local=True, tokens=tokens, cost_savings=savings)
        
        return {"text": text, "escalate": False, "reason": "success"}

    except httpx.TimeoutException:
        return {"text": "", "escalate": True, "reason": "timeout"}
    except Exception as e:
        return {"text": "", "escalate": True, "reason": f"error: {str(e)}"}


# ── Complexity Pre-screening ───────────────────────────────────────────────────
def is_complex_task(message: str) -> bool:
    """
    Quick heuristic pre-screen. If the message looks genuinely complex,
    skip Tier 0 entirely and go straight to Gemini to save time.
    """
    complexity_signals = [
        "architect", "design system", "production-grade", "scalab",
        "concurrent", "distributed", "microservice", "kubernetes",
        "novel algorithm", "from scratch", "explain how transformers",
        "mathematical proof", "optimize for performance at scale",
    ]
    message_lower = message.lower()
    return any(signal in message_lower for signal in complexity_signals)

# ── Local Agent Loop Inference ────────────────────────────────────────────────
def generate_local_json(system_prompt: str, user_prompt: str, model: str = "phi3:mini", timeout: int = 90) -> str:
    """
    Forces Ollama to return pure JSON for the local ReAct loop.
    Used exclusively by the 'Local Consultation' pipeline.
    """
    if not is_ollama_running():
        raise Exception("Ollama is offline. Cannot run local agent loop.")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = httpx.post(
            CHAT_URL,
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.2, # Lower temperature for stricter JSON
                    "num_ctx": 8192,    # Large context for code
                },
            },
            timeout=timeout,
        )
        response.raise_for_status()
        text = response.json().get("message", {}).get("content", "").strip()
        return text
    except Exception as e:
        raise Exception(f"Local LLM Error: {str(e)}")
