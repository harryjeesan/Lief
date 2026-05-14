# ============================================================
# leif/chat.py — The Main Chat Script
# ============================================================
# This is the heart of Phase 1. Run this file to talk to Leif.
#
# HOW TO RUN:
#   python -m leif.chat
#
# WHAT THIS FILE DOES (big picture):
#   1. Loads your secret API key from the .env file
#   2. Creates a connection to Claude (Anthropic's AI)
#   3. Builds a conversation history list that grows with each message
#   4. Sends your messages to Claude, wrapped in Leif's system prompt
#   5. Prints Leif's response
#   6. Loops back to step 3 until you type 'exit'
#
# LINE-BY-LINE explanations are in the comments below.
# ============================================================


# --- IMPORTS ---
# Python lets you use code written by others via "import".
# Think of imports like fetching tools from your toolbox.

import os
# 'os' is Python's built-in module for interacting with your
# operating system — reading files, environment variables, etc.

import sys
# 'sys' gives us access to the Python interpreter itself.
# We use it here to handle clean exits (sys.exit).

from dotenv import load_dotenv
# 'load_dotenv' reads your .env file and makes the values
# available as environment variables (like ANTHROPIC_API_KEY).
# This is from the 'python-dotenv' package we installed.

import anthropic
# The official Anthropic Python library. This gives us the
# 'Anthropic' class which handles all communication with Claude.

from leif.system_prompt import LEIF_SYSTEM_PROMPT
# Import Leif's personality from the other file we created.
# This keeps things organized — personality in one file,
# logic in another.


# --- CONSTANTS ---
# Constants are values that don't change during the program's run.
# Convention: write them in ALL_CAPS so they're easy to spot.

MODEL = "claude-opus-4-5"
# The specific Claude model to use.
# 'claude-opus-4-5' is Anthropic's most capable model — great for
# reasoning, coding help, and nuanced conversation.
# In Phase 2 we'll add a router to sometimes use cheaper/faster models.

MAX_TOKENS = 2048
# The maximum length of Leif's response, measured in "tokens".
# A token is roughly 0.75 words. 2048 tokens ≈ 1,500 words.
# This prevents runaway-long responses and controls API costs.

SEPARATOR = "─" * 60
# A visual divider for the terminal. Just 60 dashes in a row.
# Makes the conversation easier to read.


# --- FUNCTIONS ---
# A function is a named block of reusable code.
# You define it once, then "call" it by name whenever you need it.
# Syntax: def function_name(parameters):

def load_api_key() -> str:
    """
    Load the Anthropic API key from the .env file.
    
    Returns:
        str: The API key as a string.
    
    Raises:
        SystemExit: If the key is missing.
    
    NOTE ON THE ->  str  PART:
        This is a "type hint" — it tells you (and other developers)
        what type of value this function returns. 'str' means string
        (text). Python doesn't enforce this, but it's good practice.
    """
    # load_dotenv() reads the .env file and loads its key=value pairs
    # into the environment. After this call, os.getenv() can find them.
    load_dotenv()
    
    # os.getenv("ANTHROPIC_API_KEY") looks up that variable name.
    # If it's not found, it returns None (Python's way of saying "nothing").
    key = os.getenv("ANTHROPIC_API_KEY")
    
    # Check if the key is missing OR if the user forgot to replace
    # the placeholder text we put in the .env template.
    if not key or key == "your-anthropic-api-key-here":
        # Print a helpful error message — no jargon, just instructions.
        print("\n❌  Leif can't start — API key not found.\n")
        print("    Open your .env file and paste your Anthropic API key:")
        print("    ANTHROPIC_API_KEY=sk-ant-...\n")
        print("    Get a key at: https://console.anthropic.com/settings/keys\n")
        # sys.exit(1) stops the program with error code 1.
        # Code 0 = success. Any other number = something went wrong.
        sys.exit(1)
    
    return key


def create_client(api_key: str) -> anthropic.Anthropic:
    """
    Create and return an Anthropic API client.
    
    The client is our "connection" to Claude. Once created,
    we use it to send messages and receive responses.
    """
    return anthropic.Anthropic(api_key=api_key)


def chat_with_leif(client: anthropic.Anthropic, conversation_history: list, user_message: str) -> str:
    """
    Send a message to Claude (as Leif) and get a response.
    
    Parameters:
        client              — the Anthropic connection we created
        conversation_history — the list of all messages so far
        user_message        — what Harry just typed
    
    Returns:
        str — Leif's response text
    
    HOW CONVERSATION HISTORY WORKS:
        Claude doesn't remember your previous messages automatically.
        Every API call is stateless (a fresh start).
        
        To give Claude "memory" within a session, we maintain a list
        of all past messages and send the ENTIRE history with every
        new request. Claude reads the history and responds in context.
        
        This is exactly how ChatGPT and similar apps work under the hood.
        
        Format of each message:
        {
            "role": "user",       <- who sent it: "user" or "assistant"
            "content": "text..."  <- what they said
        }
    """
    # Add Harry's new message to the history list.
    # .append() adds an item to the end of a list.
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Send the request to Claude via the Anthropic API.
    # client.messages.create() is the main API call.
    response = client.messages.create(
        model=MODEL,                          # which Claude model to use
        max_tokens=MAX_TOKENS,                # max response length
        system=LEIF_SYSTEM_PROMPT,            # Leif's personality/instructions
        messages=conversation_history         # full conversation so far
    )
    
    # The response object contains a lot of metadata.
    # response.content is a list of "content blocks".
    # For text responses, we want the first block's text.
    leif_reply = response.content[0].text
    
    # Add Leif's reply to the history too, so the next message
    # has the full back-and-forth context.
    conversation_history.append({
        "role": "assistant",
        "content": leif_reply
    })
    
    return leif_reply


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
    print("  Phase 1: CLI Chat (Claude API)")
    print(f"{'═' * 60}")
    print("  Type your message and press Enter.")
    print("  Type 'exit' or 'quit' to end the session.")
    print(f"{'═' * 60}\n")


# --- MAIN FUNCTION ---
# By convention, the main logic of a Python program lives in a
# function called 'main()'. This keeps the code organized and
# allows other files to import from this one without running it.

def main():
    """
    The main chat loop — starts up Leif and keeps the conversation going.
    
    A "loop" in programming means: do this thing, then do it again,
    and again, until a condition tells you to stop.
    We use a 'while True' loop here — it runs forever until we
    explicitly break out of it (when the user types 'exit').
    """
    
    # --- STARTUP ---
    print_welcome()
    
    # Load the API key (will exit with instructions if missing)
    api_key = load_api_key()
    
    # Create the Claude client
    client = create_client(api_key)
    
    # Initialize an empty conversation history list.
    # [] is Python for "empty list".
    # This list will grow with each message exchanged.
    conversation_history = []
    
    print("  Connecting to Leif...\n")
    
    # --- FIRST MESSAGE ---
    # Kick off the conversation with a brief greeting from Leif.
    # We pass an empty-ish prompt to trigger her opening message.
    try:
        opening = chat_with_leif(
            client,
            conversation_history,
            "Hey Leif, we're starting a new session."
        )
        print_leif(opening)
    except anthropic.AuthenticationError:
        # This error happens when the API key is wrong or invalid.
        print("\n❌  Authentication failed — your API key is invalid.")
        print("    Double-check your .env file and try again.\n")
        sys.exit(1)
    except Exception as e:
        # 'Exception' catches any other unexpected error.
        # 'e' holds the error details so we can print them.
        print(f"\n❌  Couldn't connect to Claude: {e}\n")
        sys.exit(1)
    
    # --- MAIN CHAT LOOP ---
    # 'while True' creates an infinite loop.
    # We break out of it using 'break' when the user types 'exit'.
    while True:
        try:
            # input() displays a prompt and waits for the user to type.
            # .strip() removes any accidental leading/trailing spaces.
            user_input = input("You: ").strip()
            
            # If the user typed nothing (just pressed Enter), skip.
            if not user_input:
                continue
            
            # Check for exit commands.
            # .lower() converts to lowercase so "Exit", "EXIT", "exit"
            # all work the same way.
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n🌿 Leif: See you next time, Harry. 👋\n")
                break
            
            # Send the message to Leif and get her response.
            print("\n  Leif is thinking...", end="", flush=True)
            # end="" prevents a newline, flush=True forces it to display
            # immediately (Python normally buffers print output).
            
            reply = chat_with_leif(client, conversation_history, user_input)
            
            # Clear the "thinking..." line and print Leif's response.
            print("\r" + " " * 30 + "\r", end="")  # clear the line
            print_leif(reply)
        
        except KeyboardInterrupt:
            # This catches Ctrl+C — the user pressing Control+C to force quit.
            print("\n\n🌿 Leif: Caught off guard, Harry! See you soon. 👋\n")
            break
        
        except anthropic.RateLimitError:
            # This happens when you've sent too many requests too quickly.
            print_leif("Hold on Harry — I'm getting rate limited by the API. "
                       "Wait a moment and try again. It's not you, it's the traffic. 🚦")
        
        except Exception as e:
            # Catch-all for any other unexpected error.
            print(f"\n⚠️  Something went wrong: {e}")
            print("   Try again, or type 'exit' to quit.\n")


# --- ENTRY POINT ---
# This is a Python idiom (a common pattern) that every Python developer uses.
#
# When Python runs a file directly (python chat.py or python -m leif.chat),
# it sets a special variable __name__ to "__main__".
#
# If another file IMPORTS from this file (like: from leif.chat import something),
# __name__ will be something else, so main() won't run automatically.
#
# This lets us have a file that's both runnable AND importable. Very useful.

if __name__ == "__main__":
    main()
