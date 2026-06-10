import os
from typing import Optional
from fastapi import APIRouter, HTTPException, File, Form, UploadFile
from google.genai import types

from leif.models import ChatRequest, ChatResponse, GenerateRequest
from leif.database import save_message, get_history, create_conversation, search_memories
from leif.local_llm import query_local, is_complex_task
from leif.system_prompt import LEIF_SYSTEM_PROMPT
from leif.llm_router import generate_with_fallback

router = APIRouter()

@router.post("/api/generate")
async def generate_llm_response(request: GenerateRequest):
    """
    Headless LLM Generation for external clients (like the VS Code Extension).
    """
    try:
        response_obj = generate_with_fallback(
            contents=[{"role": "user", "parts": [{"text": request.system_prompt + "\n\n" + request.user_prompt}]}],
            is_json_mode=request.is_json_mode
        )
        return {"response": response_obj.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    message: str = Form(default=""),
    conversation_id: str = Form(default=""),
    file: Optional[UploadFile] = File(default=None),
    request: Optional[ChatRequest] = None
):
    msg_text = message if message else (request.message if request else "")
    conv_id = conversation_id if conversation_id else (request.conversation_id if request else None)
    
    if not conv_id:
        conv_id = create_conversation()
    
    try:
        lower_msg = msg_text.lower()
        if not lower_msg.startswith("/local") and (
            "we are looking for" in lower_msg or 
            "experienced developer" in lower_msg or
            "build a modern" in lower_msg or
            len(msg_text) > 250
        ):
            return ChatResponse(
                sender="model",
                content="I see you are trying to give me a complex project or an Upwork job description! Since you are currently in **Standard Chat Mode**, I can only talk to you.\n\nTo have me actually plan and build this project, please switch to **Agent Mode** (the toggle at the top of the UI) and paste your prompt there!",
                conversation_id=conv_id
            )

        raw_db_history, _ = get_history(conversation_id=conv_id)
        core_memories = search_memories(msg_text)
        current_system_prompt = LEIF_SYSTEM_PROMPT + core_memories
        
        messages_ctx = []
        for msg in raw_db_history:
            messages_ctx.append(types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["parts"][0]["text"])]))
            
        user_parts = []
        if file and file.filename:
            file_bytes = await file.read()
            mime = file.content_type or "application/octet-stream"
            
            if mime.startswith("image/"):
                user_parts.append(types.Part.from_bytes(data=file_bytes, mime_type=mime))
                user_parts.append(types.Part.from_text(text=f"{msg_text}\n\n[The user has attached an image named '{file.filename}'. Analyze it.]"))
            else:
                try:
                    file_text = file_bytes.decode("utf-8", errors="replace")
                    user_parts.append(types.Part.from_text(text=f"{msg_text}\n\n[Attached file: {file.filename}]\n```\n{file_text[:15000]}\n```"))
                except Exception:
                    user_parts.append(types.Part.from_text(text=f"{msg_text}\n\n[Attached file: {file.filename} — could not decode as text]"))
        else:
            user_parts.append(types.Part.from_text(text=msg_text))

        messages_ctx.append(types.Content(role="user", parts=user_parts))

        gemini_succeeded = False
        final_text = None
        local_llm_enabled = os.getenv("LOCAL_LLM_ENABLED", "true").lower() == "true"
        ollama_model = os.getenv("OLLAMA_MODEL", "phi3:mini")

        if local_llm_enabled and not is_complex_task(msg_text) and not (file and file.filename):
            print(f"[Tier 0] Attempting local inference with {ollama_model}...")
            local_result = query_local(
                prompt=msg_text,
                model=ollama_model,
                system_prompt=current_system_prompt,
            )
            if not local_result["escalate"]:
                final_text = local_result["text"]
                print(f"[Tier 0] ✅ Handled locally. Reason: {local_result['reason']}")
            else:
                print(f"[Tier 0] ⬆️  Escalating to Gemini. Reason: {local_result['reason']}")
        else:
            print(f"[Tier 0] Skipped (complex task or file attached — going straight to Gemini)")

        if final_text is None:
            try:
                thinking_config = types.GenerateContentConfig(
                    system_instruction=current_system_prompt,
                    thinking_config=types.ThinkingConfig(thinking_budget=8192)
                )
                response = generate_with_fallback(messages_ctx, config=thinking_config)
                final_text = response.text
            except Exception as e:
                print(f"Router exhausted all fallbacks: {e}")
                final_text = "⚠️ Leif Core Error: All AI models are currently down or rate limited. Please check your API keys or try again later."

        save_message("user", msg_text + (f" [attached: {file.filename}]" if file and file.filename else ""), conversation_id=conv_id)
        save_message("leif", final_text, conversation_id=conv_id)
        
        return ChatResponse(response=final_text, conversation_id=conv_id)
        
    except Exception as e:
        print(f"Error communicating with AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))
