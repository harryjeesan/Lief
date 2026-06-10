import os
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Configuration via env vars
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL") # e.g. http://localhost:8000/generate
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Leads")
ONBOARDING_URL = os.getenv("ONBOARDING_URL") # Fillout or generic webhook
ONBOARDING_API_KEY = os.getenv("ONBOARDING_API_KEY")
STRIPE_PAYMENT_LINK = os.getenv("STRIPE_PAYMENT_LINK", "https://buy.stripe.com/test_hardcoded_link")

# Basic request models
class SmartLeadPayload(BaseModel):
    email: str
    body: str
    subject: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class StripeWebhookPayload(BaseModel):
    type: str
    data: Dict[str, Any]

async def call_local_llm(prompt: str) -> str:
    if not LOCAL_LLM_URL:
        raise RuntimeError("LOCAL_LLM_URL not configured")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(LOCAL_LLM_URL, json={"input": prompt})
        resp.raise_for_status()
        data = resp.json()
        return data.get("output") or data.get("text") or str(data)

async def call_openai_chat(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        j = r.json()
        return j["choices"][0]["message"]["content"].strip()

async def analyze_intent(text: str) -> str:
    prompt = (
        "You are an intent classifier. Given the following cold email reply, respond with a single word: 'positive', 'neutral', or 'negative'.\n\n"
        f"Email reply:\n{text}\n\nReply with only one word."
    )
    try:
        if LOCAL_LLM_URL:
            out = await call_local_llm(prompt)
        else:
            out = await call_openai_chat(prompt)
    except Exception as e:
        logging.exception("LLM intent call failed")
        raise
    if not out:
        return "neutral"
    o = out.strip().lower()
    for token in ("positive", "negative", "neutral"):
        if token in o: return token
    if any(w in o for w in ("yes", "interested", "sure", "let's", "yes please", "count me in")):
        return "positive"
    return "neutral"

async def generate_reply(lead_body: str) -> str:
    prompt = (
        "You are a helpful assistant. Write a short, casual reply to the prospect based on their email reply, inviting them to complete a quick payment to get started."
        f" Include this payment link verbatim: {STRIPE_PAYMENT_LINK}. Keep it friendly and concise.\n\nProspect reply:\n{lead_body}"
    )
    try:
        if LOCAL_LLM_URL:
            return await call_local_llm(prompt)
        return await call_openai_chat(prompt)
    except Exception:
        logging.exception("LLM generate reply failed")
        return (
            "Thanks for your reply! We'd love to get you started — you can complete the onboarding via this link: "
            f"{STRIPE_PAYMENT_LINK}"
        )

async def log_to_airtable(email: str, intent_status: str, raw_body: str) -> None:
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        logging.info("Airtable not configured; skipping log")
        return
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{httpx.utils.quote(AIRTABLE_TABLE_NAME, safe='')}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"fields": {"Email": email, "IntentStatus": intent_status, "RawBody": raw_body}}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            logging.info("Logged to Airtable for %s", email)
    except Exception:
        logging.exception("Failed to log to Airtable")

async def trigger_onboarding(email: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    if not ONBOARDING_URL:
        logging.info("Onboarding URL not configured; skipping trigger")
        return
    headers = {"Content-Type": "application/json"}
    if ONBOARDING_API_KEY:
        headers["Authorization"] = f"Bearer {ONBOARDING_API_KEY}"
    payload = {"email": email, "metadata": metadata or {}}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(ONBOARDING_URL, json=payload, headers=headers)
            r.raise_for_status()
            logging.info("Triggered onboarding for %s", email)
    except Exception:
        logging.exception("Failed to trigger onboarding")

@app.post("/webhook/smartlead")
async def webhook_smartlead(payload: SmartLeadPayload, background_tasks: BackgroundTasks):
    try:
        intent = await analyze_intent(payload.body)
    except Exception:
        raise HTTPException(status_code=500, detail="Intent analysis failed")

    generated_reply = None
    if intent == "positive":
        try:
            generated_reply = await generate_reply(payload.body)
        except Exception:
            logging.exception("Failed to generate reply")
            generated_reply = (
                "Thanks for your reply! To get started, please complete the payment here: "
                f"{STRIPE_PAYMENT_LINK}"
            )
    background_tasks.add_task(log_to_airtable, payload.email, intent, payload.body)
    return {
        "status": "ok",
        "intent": intent,
        "generated_reply": generated_reply,
    }

@app.post("/webhook/stripe")
async def webhook_stripe(payload: dict, request: Request, background_tasks: BackgroundTasks):
    event_type = payload.get("type")
    data = payload.get("data", {})
    success_events = {"payment_intent.succeeded", "checkout.session.completed"}
    
    if event_type in success_events:
        obj = data.get("object", {})
        email = obj.get("customer_email") or obj.get("receipt_email") or obj.get("metadata", {}).get("email")
        if not email:
            email = payload.get("data", {}).get("object", {}).get("customer_details", {}).get("email")
        if not email:
            logging.warning("Stripe success event without email; skipping onboarding trigger")
            return {"status": "ignored", "reason": "no_email_found"}
        background_tasks.add_task(trigger_onboarding, email, obj.get("metadata"))
        return {"status": "ok", "email": email}
    return {"status": "ignored", "event_type": event_type}

@app.get("/")
async def root():
    return {"status": "running"}
