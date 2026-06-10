# ============================================================
# leif/chat.py — The Main Chat Script (Gemini Edition)
# ============================================================
# This is the heart of Phase 1. Run this file to talk to Leif.
#
# HOW TO RUN:
#   python -m leif.chat
# ============================================================

import os
import sys

# FIX: Force Windows terminals to use UTF-8 encoding so emojis
# like 🌿 and borders like ═ don't crash the script!
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from google import genai
from leif.system_prompt import LEIF_SYSTEM_PROMPT

MODEL = "gemini-2.5-flash"
SEPARATOR = "─" * 60

def load_api_key() -> str:
    """Load the Gemini API key from the .env file."""
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    
    if not key or key == "your_actual_key_goes_here":
        print("\n❌  Leif can't start — API key not found.\n")
        print("    Open your .env file and paste your Gemini API key:")
        print("    GEMINI_API_KEY=AIzaSy...\n")
        print("    Get a free key at: https://aistudio.google.com/app/apikey\n")
        sys.exit(1)
    
    return key

def create_client(api_key: str):
    """Configure the modern Google GenAI Client."""
    # We use the modern google-genai SDK 
    client = genai.Client(api_key=api_key)
    return client

def print_leif(message: str):
    """Print Leif's message with visual formatting."""
    print(f"\n{SEPARATOR}")
    print(f"🌿 Leif\n")
    print(message)
    print(f"{SEPARATOR}\n")

def print_welcome():
    """Print the startup banner."""
    print(f"\n{'═' * 60}")
    print("  🌿  LEIF — Your Personal AI Assistant")
    print("  Phase 1: CLI Chat (Free Gemini API)")
    print(f"{'═' * 60}")
    print("  Type your message and press Enter.")
    print("  Type 'exit' or 'quit' to end the session.")
    print(f"{'═' * 60}\n")

def main():
    print_welcome()
    
    api_key = load_api_key()
    client = create_client(api_key)
    
    # Start a chat session using the modern SDK
    chat = client.chats.create(
        model=MODEL,
        config={"system_instruction": LEIF_SYSTEM_PROMPT}
    )
    
    print("  Connecting to Leif...\n")
    
    try:
        response = chat.send_message("Hey Leif, we're starting a new session.")
        print_leif(response.text)
    except Exception as e:
        print(f"\n❌  Couldn't connect to Gemini: {e}\n")
        sys.exit(1)
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n🌿 Leif: See you next time, Harry. 👋\n")
                break
            
            print("\n  Leif is thinking...", end="", flush=True)
            
            # Send the message to Gemini
            response = chat.send_message(user_input)
            
            print("\r" + " " * 30 + "\r", end="")  # clear the thinking line
            print_leif(response.text)
        
        except KeyboardInterrupt:
            print("\n\n🌿 Leif: Caught off guard, Harry! See you soon. 👋\n")
            break
        except Exception as e:
            print(f"\n⚠️  Something went wrong: {e}")
            print("   Try again, or type 'exit' to quit.\n")

if __name__ == "__main__":
    main()
