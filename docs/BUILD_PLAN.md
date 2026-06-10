# 🌿 Leif — The Complete Build Plan
*From today's AI assistant to a fully autonomous commercial software development agent*

---

## The Goal

By the end of this plan, Leif will be capable of:
- Writing, running, debugging, and verifying real software autonomously
- Building complete SaaS products (frontend + backend + auth + billing + hosting scripts)
- Operating mostly offline and free using local models
- Remembering everything about you, your projects, and your decisions permanently
- Reading, summarizing, and understanding large external codebases
- Escalating to powerful cloud models (Gemini, DeepSeek) only when she genuinely needs it

---

## Phase Overview

```
Current Leif        ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
(Cloud only,            (Local     (Training    (Web        (Code
 no memory,              LLM,       Data         Retrieval    Analyzer
 no tools)               offline)   Export)      API)         + Sandbox)
                                                              │
                                                              ▼
                    Phase 9 ◄── Phase 8 ◄── Phase 7 ◄── Phase 5/6
                   (Hardening   (Vector    (ReAct       (Codebase
                    + Launch)    Memory)    Agent        Intelligence
                                           Loop)        Sub-System)
```

---

## Phase 1 — Local LLM: Wiring Tier 0 (Ollama + Phi-3 Mini)

### What You Are Building
A locally running AI model that serves as the first responder for every message,
running entirely free and offline before any cloud call is attempted.

### Why First?
Everything else — the sandbox, the agent loop, the fine-tuning — depends on having
a working local inference engine. This is the foundation.

### Steps

**Step 1A — Install Ollama**
1. Download Ollama from https://ollama.com (Windows installer)
2. Run: `ollama pull phi3:mini`
3. Verify with: `ollama run phi3:mini "Hello, say hi in one sentence."`

**Step 1B — Create `leif/local_llm.py`**

New module that wraps the Ollama HTTP API:
```python
# leif/local_llm.py
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
ESCALATION_PHRASES = [
    "i don't know", "i'm not sure", "i cannot", "i'm unable",
    "i don't have access", "as a language model", "beyond my capabilities"
]

def query_local(prompt: str, model: str = "phi3:mini", timeout: int = 15) -> dict:
    """
    Sends a prompt to the local Ollama model and returns:
    { "text": "...", "escalate": True/False }
    """
    try:
        response = httpx.post(OLLAMA_URL, json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }, timeout=timeout)
        text = response.json().get("response", "")

        escalate = (
            len(text.strip()) < 20 or
            any(phrase in text.lower() for phrase in ESCALATION_PHRASES) or
            text.count("```") % 2 != 0  # Unclosed code block
        )
        return {"text": text, "escalate": escalate}
    except Exception:
        return {"text": "", "escalate": True}  # Offline → escalate to Gemini
```

**Step 1C — Modify `leif/api.py`**
- Add `LOCAL_LLM_ENABLED` and `OLLAMA_MODEL` config from `.env`
- Before the Gemini block in `/api/chat`, attempt the local model first
- If `escalate=True`, proceed with existing Gemini routing unchanged
- Add a `/api/local-status` endpoint for the UI pill

**Step 1D — Add `.env` Config**
```env
LOCAL_LLM_ENABLED=true
OLLAMA_MODEL=phi3:mini
```

**Step 1E — Update `frontend/src/App.jsx`**
- Add a `LOCAL ✓` / `LOCAL ✗` green/grey pill to the Key Status Panel
- Poll `/api/local-status` every 30 seconds alongside key status

### What Leif Can Do After Phase 1
✅ Simple questions answered instantly offline at zero cost
✅ Boilerplate code written locally without using any API quota
✅ Gemini is only called for genuinely complex tasks

### Hardware Usage
| Resource | Usage |
|---|---|
| VRAM | ~2.3GB (Phi-3 Mini lives in GPU memory) |
| RAM | ~500MB additional |
| CPU | Idle when not generating |

---

## Phase 2 — Training Data Export

### What You Are Building
A script that reads your conversation history from `leif_memory.db` and formats it
as a clean dataset for fine-tuning Leif to know you specifically.

### Steps

**Step 2A — Create `scripts/export_training_data.py`**
```python
# Connects to D:\Leif_Data\leif_memory.db (or local leif_memory.db)
# Extracts all conversation pairs
# Filters: removes exchanges under 20 characters on either side
# Formats as JSONL for Unsloth:
# {"conversations": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
# Saves to: scripts/training_data.jsonl
# Prints: N conversations, M pairs, ~X tokens
```

**Step 2B — Run the Script**
```powershell
python scripts/export_training_data.py
```

### What Leif Can Do After Phase 2
✅ Training dataset ready for upload to Google Colab
✅ Can audit exactly what Leif "knows" about you

---

## Phase 3 — Fine-Tuning on Colab (Your Personal Leif Brain)

### What You Are Building
A custom GGUF model file that is Phi-3 Mini, but fine-tuned on your specific
conversations, coding patterns, and preferences. This becomes Leif's permanent
offline brain — one that writes code the way YOU write it.

### Steps

**Step 3A — Create `scripts/leif_finetune.ipynb`**

Pre-built Colab notebook with the following cells ready to run:
1. Install Unsloth: `pip install unsloth`
2. Load `microsoft/Phi-3-mini-4k-instruct` as the base model
3. Configure QLoRA (4-bit quantization, targeting your 4GB VRAM for loading)
4. Upload and load `training_data.jsonl`
5. Train for 1–3 epochs (~1 hour on Colab A100, ~3 hours on T4)
6. Merge LoRA adapter into base model
7. Export as GGUF (Q4_K_M quantization — optimal for 4GB VRAM)
8. Download `leif-finetuned.gguf` to your PC

**Step 3B — Create `scripts/Modelfile`**
```
FROM ./leif-finetuned.gguf
SYSTEM "You are Leif, Harry's personal software development assistant..."
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
```

**Step 3C — Load into Ollama**
```powershell
ollama create leif-local -f scripts/Modelfile
```

**Step 3D — Update `.env`**
```env
OLLAMA_MODEL=leif-local
```

### What Leif Can Do After Phase 3
✅ Responds in her own voice, trained on your actual conversations
✅ Writes Python/React code matching your personal conventions automatically
✅ Understands Leif's own project structure from training

---

## Phase 4 — Web Retrieval API (Built From Scratch)

### What You Are Building
A targeted web intelligence engine for fetching accurate, up-to-date documentation
from technical sources. This eliminates hallucinated API methods forever.

### Steps

**Step 4A — Create `leif/web_retrieval.py`**

Topic router that detects query type and targets the correct source:
```python
# Query: "stripe create subscription" → stripe.com/docs
# Query: "ModuleNotFoundError: requests" → PyPI + StackOverflow
# Query: "React useEffect infinite loop" → react.dev + StackOverflow
# Query: "git rebase conflict" → GitHub docs + StackOverflow
```

Fetching stack:
- `httpx` for fast HTTP requests
- `trafilatura` for clean article text extraction
- `BeautifulSoup` for HTML parsing when trafilatura fails
- DuckDuckGo HTML scraping as the general fallback

**Step 4B — Add `/api/search` Endpoint**
- Accepts a query string
- Routes to the correct source automatically
- Returns a clean, structured `{source, title, url, content}` payload to the brain

**Step 4C — Wire into the Chat Endpoint**
- When Leif detects a technical question (library, error, framework), she calls
  the web retrieval tool before generating her answer
- The retrieved docs are injected into the prompt as context

### What Leif Can Do After Phase 4
✅ No more hallucinated library methods — she reads the actual docs
✅ Always current — not limited by training cutoff dates
✅ Zero API cost — scrapes public web at £0

---

## Phase 5 — Code Analyzer (Deterministic Error Detection)

### What You Are Building
A tool that runs real linters and type checkers against code — producing exact,
line-level error lists rather than guessed feedback.

### Steps

**Step 5A — Create `leif/code_analyzer.py`**

Runs multiple linters in one call:
```python
# Python: pylint + flake8 + mypy
# JavaScript/TypeScript: ESLint + tsc
# Returns structured JSON:
# [{"file": "api.py", "line": 42, "error": "undefined variable", "severity": "error"}]
```

**Step 5B — Add `/api/analyze` Endpoint**
- Accepts raw code string or a file path
- Returns structured error list

**Step 5C — Wire into Agent Loop**
- After every code generation step, the analyzer runs automatically
- If errors exist, they are fed back into the next prompt iteration

### What Leif Can Do After Phase 5
✅ Catches syntax and type errors before showing code to you
✅ Error feedback loop: generate → analyze → fix → analyze again

---

## Phase 6 — Sandbox + Debugger (Code That Verifies Itself)

### What You Are Building
A safe execution environment that actually runs the code Leif writes, plus a
structured debugger that reads stack traces and identifies the exact fix.

### Steps

**Step 6A — Create `leif/sandbox.py`**
```python
# Uses Python subprocess to run code in an isolated call
# Captures: stdout, stderr, exit_code, execution_time
# Enforces a 30-second timeout
# Returns: {"output": "...", "error": "...", "success": True/False}
```

**Step 6B — Create `leif/debugger.py`**
```python
# Parses a raw Python/Node stack trace
# Classifies the error type: ImportError, TypeError, NetworkError, etc.
# Extracts: file name, line number, the failing expression
# Returns: {"error_type": "...", "line": 42, "suggestion": "..."}
```

**Step 6C — Add `/api/run` and `/api/debug` Endpoints**

**Step 6D — Wire into the Chat Endpoint**
- Code blocks in responses are automatically tested in the sandbox
- If the sandbox returns an error, the debugger classifies it and feeds the
  diagnosis back into the next generation step

### What Leif Can Do After Phase 6
✅ Every piece of code Leif shows you has already been tested and runs
✅ No more "this should work" — Leif knows it works because she ran it
✅ Debugging loop is fully autonomous (generate → run → debug → fix → run)

---

## Phase 7 — Codebase Intelligence Sub-System (3-Tool Pipeline)

### What You Are Building
The three-tool pre-processor that lets Leif understand your entire project without
ever overflowing the local model's 4K context window.

### Steps

**Step 7A — Create `leif/codebase_reader.py` (Tool 1: The Reader)**
```python
# Uses Python's ast module to parse .py files into logical blocks
# Uses a JS parser (esprima or acorn) for .js/.tsx files
# Outputs: list of {name, type, code, file, line_start, line_end}
```

**Step 7B — Install and Pull the Summarizer Model**
```powershell
ollama pull qwen2.5-coder:1.5b
```

**Step 7C — Create `leif/codebase_summarizer.py` (Tool 2: The Understander)**
```python
# Sequentially feeds each code block to qwen2.5-coder:1.5b via Ollama
# Generates a 1–3 sentence plain English description for each block
# Outputs: {name, summary, file, type}
```

**Step 7D — Create `leif/codebase_compiler.py` (Tool 3: The Compiler)**
```python
# Aggregates all summaries into a structured index map
# Builds a simple import graph (which files import which)
# Stores vector embeddings in ChromaDB for semantic search
# Outputs a compressed 2KB "Codebase Intelligence Report" on demand
```

**Step 7E — Wire into Agent Loop**
- When Harry starts a new coding task, the compiler runs a project scan
- The 2KB report is injected into Leif's prompt as project context

### What Leif Can Do After Phase 7
✅ Reads your entire project regardless of how many files it has
✅ Cross-references your code style, imports, and function signatures
✅ Understands large third-party codebases (like an open-source library you want to extend)

---

## Phase 8 — ReAct Agent Loop + Agent Mode UI

### What You Are Building
The autonomous reasoning loop that makes Leif an agent, not just a chatbot.
ReAct = Reason + Act, in a verified loop.

### Steps

**Step 8A — Create `leif/agent.py`**

The core ReAct loop:
```python
def agent_loop(task: str, max_iterations: int = 5):
    for i in range(max_iterations):
        # THINK: What does Leif need to do next?
        thought = generate_thought(task, history)

        # ACT: Pick and execute a tool
        tool, args = parse_tool_call(thought)
        result = execute_tool(tool, args)

        # OBSERVE: Did it work?
        history.append({"thought": thought, "action": tool, "result": result})

        if result.get("success") and result.get("final"):
            return result  # Done!

    return {"error": "Max iterations reached — needs Harry's input"}
```

**Available tools the agent can call:**
- `web_retrieval(query)` — fetch documentation
- `code_analyzer(code)` — lint and type-check code
- `sandbox_run(code)` — execute code
- `debugger(error)` — classify and fix errors
- `codebase_read(path)` — read a project file
- `file_write(path, content)` — write a file (approval-gated)
- `terminal_run(command)` — run a shell command (approval-gated)

**Step 8B — Add `/api/agent` Streaming Endpoint**
- Returns server-sent events (SSE) so you see each thought and action in real time
- Uses `async generator` to stream the loop steps as they happen

**Step 8C — Update the Frontend for Agent Mode**
- Add an "Agent Mode" toggle in the React UI
- When active, the chat window switches to a live feed showing:
  - `🧠 Thinking...`
  - `🌐 Fetching Stripe docs...`
  - `🔧 Running code in sandbox...`
  - `❌ Error caught — debugging...`
  - `✅ Fix applied — re-running...`
  - `📄 Ready for your approval`
- Approval gate modal: shows a diff of every file Leif wants to write

### What Leif Can Do After Phase 8
✅ End-to-end autonomous development — you describe a task, she delivers working code
✅ Full transparency — you see every step of her thinking and acting in real time
✅ Safety guaranteed — file writes and terminal commands always require your click

---

## Phase 9 — ChromaDB Vector Memory (Permanent Semantic Recall)

### What You Are Building
Long-term memory that searches across every past conversation semantically —
not just by keyword, but by meaning.

### Steps

**Step 9A — Install ChromaDB**
```powershell
pip install chromadb sentence-transformers
```

**Step 9B — Create `leif/vector_memory.py`**
```python
# On every new message saved: generate a vector embedding and store in ChromaDB
# On every new session: search ChromaDB for past conversations relevant to the
#   current topic and inject top 3 results as context automatically
```

**Step 9C — Wire into `/api/chat`**
- Before every generation, query ChromaDB: "What has Harry asked about this topic before?"
- Inject the top 3 past answers into the system prompt as memory context

**Step 9D — Add a Memory Panel to the UI**
- Show a collapsible "Memories Used" section on each response
- Let Harry click to see which past conversations are being recalled

### What Leif Can Do After Phase 9
✅ Never forgets a decision, a preference, or a past discussion
✅ Cross-references past projects when building new ones
✅ Grows smarter the longer you use her — each conversation makes the next one better

---

## Phase 10 — Hardening, Tuning & Production Polish

### What You Are Building
The final 10% that turns a working prototype into a polished, reliable tool
you depend on daily.

### Steps

**Step 10A — Error Recovery**
- Add graceful handling for when Ollama crashes or runs out of VRAM
- Add retry logic with exponential backoff for all external API calls

**Step 10B — Performance Tuning**
- Cache web retrieval results for 24 hours (so repeated library lookups are instant)
- Pre-warm the local model on startup (load it into VRAM before you send the first message)

**Step 10C — Context Window Management**
- Add a smart trimmer that compresses old conversation history into summaries
  before it hits the 4K context limit of the local model

**Step 10D — Metrics Dashboard (UI)**
- Add a simple stats panel showing:
  - % of requests handled locally (free) vs. escalated to cloud
  - Total tokens saved vs. cloud-only equivalent
  - Total estimated $ cost this month

**Step 10E — Re-Fine-Tune After 6 Months**
- Export the new conversations from `leif_memory.db` (which now has 6 more months of data)
- Run a second fine-tuning pass on Colab to update Leif's brain with your newer work
- Replace the old GGUF file with the new one — Leif gets smarter over time

---

## Complete Timeline Estimate

| Phase | Estimated Time | Dependency |
|---|---|---|
| **Phase 1** — Local LLM (Ollama) | 2–3 hours | Download Ollama first |
| **Phase 2** — Training Data Export | 1 hour | Phase 1 complete |
| **Phase 3** — Colab Fine-Tuning | 1–3 hours (runs overnight) | Phase 2 complete |
| **Phase 4** — Web Retrieval API | 3–4 hours | Phase 1 complete |
| **Phase 5** — Code Analyzer | 2–3 hours | Phase 1 complete |
| **Phase 6** — Sandbox + Debugger | 3–4 hours | Phase 5 complete |
| **Phase 7** — Codebase Intelligence (3-Tool Pipeline) | 4–5 hours | Phase 6 + ChromaDB installed |
| **Phase 8** — ReAct Agent Loop + UI | 6–8 hours | Phases 4, 5, 6, 7 complete |
| **Phase 9** — Vector Memory (ChromaDB) | 2–3 hours | Phase 1 complete |
| **Phase 10** — Hardening | 3–4 hours | All phases complete |
| **TOTAL** | **~30–40 hours of development** | Spread across weeks |

---

## What Leif Can Build After All Phases Complete

| Project Type | Capable? | How |
|---|---|---|
| Personal tools (CLI apps, utilities) | ✅ Fully autonomous | Phases 5, 6, 8 |
| Web apps (React + FastAPI) | ✅ Fully autonomous | Phases 4, 5, 6, 7, 8 |
| AI-powered tools (like mini-Cluely) | ✅ Collaborative | Phases 4, 6, 8 + Gemini cascade |
| Medical imaging tools (root canal detector) | ✅ Collaborative | Phases 4, 6, 8 + Gemini cascade |
| Full SaaS products (auth + billing + hosting) | ✅ Collaborative | All phases |
| Mobile apps (React Native) | ⚠️ Partial — needs testing on device | Phases 4, 8 |
| Game engines | ❌ Too complex for local model | Escalates entirely to Gemini |

---

## Next Concrete Step

**Start Phase 1 right now.**

1. Download Ollama from https://ollama.com
2. Pull the model: `ollama pull phi3:mini`
3. Tell Leif: *"Let's begin Phase 1 — wire the local LLM into the API"*
4. Leif writes `local_llm.py`, modifies `api.py`, updates the frontend pill
5. Test: send a simple message → verify it responds locally (no Gemini request in logs)

Everything else builds on this single foundation. Once the local model is running,
every subsequent phase can be added incrementally without breaking anything.

---

*This is the plan. Built with intent by Harry.*
