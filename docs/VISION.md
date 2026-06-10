# 🌿 Leif — The Complete Vision
*The full architecture of what Leif becomes*

---

## The One-Line Summary

> Leif is a private, offline-capable, self-improving software development agent that knows Harry specifically, fetches what she doesn't know from the internet, writes code, runs it, debugs it autonomously, and only asks for help when she genuinely needs it.

---

## The Full Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Harry                                       │
│                    React Web UI (localhost:5173)                    │
│     Chat │ Agent Mode Feed │ Approval Gates │ Key Status Panel     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────────────┐
│                    FastAPI Backend (localhost:8000)                  │
│                         leif/api.py                                 │
└──────┬─────────────────────────┬──────────────────────────┬─────────┘
       │                         │                          │
┌──────▼──────────┐   ┌──────────▼────────────┐   ┌───────▼──────────┐
│   BRAIN LAYER   │   │    TOOL SUITE         │   │  MEMORY LAYER    │
│                 │   │                       │   │                  │
│ Tier 0          │   │ Web Retrieval API     │   │ SQLite           │
│ Local Fine-tuned│   │  - DuckDuckGo        │   │ (conversations)  │
│ Phi-3 Mini 3.8B │   │  - StackOverflow API │   │                  │
│ (offline, free) │   │  - GitHub API        │   │ ChromaDB         │
│       ↓         │   │  - PyPI / npm API    │   │ (semantic search │
│ Tier 1          │   │  - Direct doc fetch  │   │  across all past │
│ Gemini 2.5 Flash│   │                       │   │  conversations)  │
│ + Thinking Mode │   │ Code Analyzer        │   │                  │
│       ↓         │   │  - pylint, flake8    │   │ Project Index    │
│ Tier 2          │   │  - mypy, ESLint, tsc │   │ (live codebase   │
│ Gemini Flash    │   │                       │   │  file tree,      │
│ Lite            │   │ Sandbox / Runner     │   │  signatures,     │
│       ↓         │   │  - subprocess exec   │   │  imports)        │
│ Tier 3          │   │  - structured output │   │                  │
│ Groq Llama 3.3  │   │                       │   └──────────────────┘
│ 70B             │   │ Debugger             │
│                 │   │  - stack trace parse │
└─────────────────┘   │  - error classifier  │
                      │  - fix suggestions   │
                      │                       │
                      │ Project Mapper        │
                      │  - file tree          │
                      │  - import graph       │
                      │  - function sigs      │
                      │                       │
                      │ Browser Subagent      │
                      │  - Playwright         │
                      │  - DOM inspection     │
                      │                       │
                      │ Terminal Tool         │
                      │  - PowerShell exec    │
                      └───────────────────────┘
                                │
              ┌─────────────────▼──────────────────┐
              │         REACT AGENT LOOP            │
              │                                     │
              │  THINK → FETCH → COMPILE            │
              │    → GENERATE → RUN → DEBUG         │
              │         ↑_________________|         │
              │  Loop until ✅ or max iterations    │
              └─────────────────────────────────────┘
```

---

## Component Breakdown

### 1. The Brain — 4-Tier Intelligence Router

The brain selects the right AI for every task automatically.

| Tier | Model | When Used | Cost |
|---|---|---|---|
| **0** | Local fine-tuned Phi-3 Mini 3.8B | Always first — knows Harry's patterns, runs offline | Free forever |
| **1** | Gemini 2.5 Flash + Thinking | Tier 0 escalates, or task is genuinely complex | API quota |
| **2** | Gemini Flash Lite | Tier 1 quota exhausted | API quota |
| **3** | Groq Llama 3.3 70B | All Gemini keys exhausted | Free (14,400/day) |

**Fine-tuning makes Tier 0 specifically trained on:**
- Harry's coding patterns and preferences
- Leif's exact personality and tone
- The Leif project's codebase and conventions
- All past conversations from `leif_memory.db`

Trained via Colab Pro (A100 GPU) using Unsloth + QLoRA. Exported as GGUF. Loaded into Ollama locally on Harry's RTX 3050 (optimized for 4GB VRAM).

---

### 2. The Web Retrieval API — Built From Scratch

A targeted web intelligence engine. Not a general search engine — a precision fetcher for exactly the domains Leif works in.

**Sources:**
| Source | API Type | Cost |
|---|---|---|
| Stack Overflow | StackExchange API — public, no key | £0 |
| GitHub | REST API — 60 req/hr free | £0 |
| Python docs | Direct HTTP + trafilatura extraction | £0 |
| FastAPI / React / MDN docs | Direct HTTP + trafilatura extraction | £0 |
| PyPI packages | Public JSON API | £0 |
| npm packages | Public JSON API | £0 |
| General web | DuckDuckGo HTML scrape | £0 |

**Topic Router** — detects query type and targets the right source:
```
"ModuleNotFoundError: no module named X"  → PyPI + StackOverflow
"How do I use useEffect in React?"         → react.dev + StackOverflow
"FastAPI 422 Unprocessable Entity"         → FastAPI docs + StackOverflow
"git rebase vs merge"                      → GitHub docs + StackOverflow
```

**Total external API cost: £0.**

---

### 3. The Tool Suite

Specialized programs for deterministic tasks — faster and more accurate than asking an LLM to guess.

#### Code Analyzer
Runs multiple linters in one call:
- **Python:** `pylint` + `flake8` + `mypy`
- **JavaScript/React:** `ESLint` + TypeScript compiler
- **Returns:** `[{line: 12, error: "undefined variable", severity: "error", suggestion: "..."}]`

#### Sandbox / Code Runner
Safely executes code and returns real output — not a simulation:
- Subprocess execution with timeout
- Captures stdout, stderr, exit code, execution time
- No file system writes without approval

#### Debugger
Parses execution failures into structured intelligence:
- Stack trace line extraction
- Error type classification (ImportError, TypeError, NetworkError, etc.)
- Suggests targeted fix based on error pattern
- Feeds diagnosis back into the agent loop

#### Project Structure Mapper
Gives the brain a full map of Harry's codebase:
- File tree with sizes
- Import graph (what imports what)
- Function and class signatures
- Called automatically at the start of complex coding tasks

#### Browser Subagent (existing, upgraded)
- Playwright Chromium automation
- DOM inspection via `browser_utils.py`
- Approval-gated (reads DOM autonomously, actions require approval)

#### Terminal Tool (existing)
- PowerShell command execution
- Output fed back into brain context
- Approval-gated

---

### 4. The ReAct Agent Loop

The system that makes Leif an **autonomous developer**, not just a chatbot.

**ReAct = Reasoning + Acting in a loop.**

```
Harry: "Build me a WebSocket endpoint for real-time notifications"

Iteration 1:
  THINK:    "I need WebSocket docs for FastAPI"
  FETCH:    Web Retrieval → fastapi.tiangolo.com/websockets
  COMPILE:  Merge docs with Harry's existing api.py structure
  GENERATE: Write websocket_router.py
  RUN:      Sandbox executes it
  RESULT:   ❌ ImportError — 'websockets' not found

Iteration 2:
  THINK:    "Missing dependency. Fix import, install package"
  FETCH:    PyPI API → websockets package info
  DEBUG:    "Need websockets>=10.4 in requirements.txt"
  GENERATE: Fix import, update requirements.txt
  RUN:      Sandbox re-executes
  RESULT:   ✅ Server running on ws://localhost:8001

Output to Harry:
  - Working websocket_router.py
  - Updated requirements.txt
  - Explanation of what was built and why
  - "Click to approve writing files to disk"
```

**Guardrails:**
- Maximum 5 iterations per task
- 30-second timeout per sandbox run
- File writes always require Harry's approval
- Harry sees every step in real time in the UI

---

### 5. The Memory Layer

Three levels of memory — each serving a different time horizon.

| Layer | Technology | Scope | Speed |
|---|---|---|---|
| **Conversation** | SQLite (existing) | Full message history, all sessions | Instant |
| **Semantic** | ChromaDB (planned) | Search across all past conversations by meaning | Fast |
| **Project** | Live file indexing (planned) | Current state of Harry's codebase | On-demand |

**Vector memory example:**
```
Harry: "What did we decide about the auth system last month?"

Without ChromaDB: Leif can't remember (it's not in the current conversation)
With ChromaDB:    Leif searches semantically → finds the relevant conversation
                  → "In February, we decided on JWT with a 7-day refresh token
                      stored in httpOnly cookies because..."
```

---

### 6. Codebase Intelligence Sub-System (3-Tool Pipeline)

A dedicated, lightweight pre-processing engine designed to give Leif a comprehensive understanding of large codebases without overflowing the local model's 4K context window or slowing down inference.

```
┌─────────────────────────────────────────────────────────────────┐
│                       RAW CODEBASE                              │
│  api.py (456 lines) | local_llm.py (120 lines) | ...            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                  [Tool 1: Reader (Chunker)]
                  - Splits files using AST parsing
                  - Extracts logical functions/classes
                                │
                                ▼
               [Tool 2: Understander (Summarizer)]
               - Uses an ultra-lightweight local model
                 (e.g., Qwen2.5-Coder 1.5B, ~1.2GB VRAM)
               - Sequentially describes each code block
                                │
                                ▼
                 [Tool 3: Compiler (Brain)]
               - Compiles chunk summaries into a structured,
                 highly compressed "Codebase Index" map
               - Stores vector definitions in ChromaDB
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LEIF MAIN BRAIN (Phi-3 Mini)                   │
│  Reads the 2KB compiled intelligence map instead of raw files.  │
│  Has 100% codebase context using only 5% of the token cost.     │
└─────────────────────────────────────────────────────────────────┘
```

* **Tool 1: The Reader (Chunker):** Uses Python's native `ast` parser to parse code structure. It runs in milliseconds on the CPU and produces clean, isolated function and class definitions.
* **Tool 2: The Understander (Summarizer):** Takes code chunks and runs them sequentially through a fast, lightweight local model (like `qwen2.5-coder:1.5b` running in Ollama at ~45 tokens/sec). Because it works sequentially, it never runs out of VRAM or context space.
* **Tool 3: The Compiler (Brain):** Aggregates all block summaries, builds an import and call-graph map, and indexes them semantically in ChromaDB. When Leif needs to answer a question, she queries the compiler's output map instead of the raw code.

---

## What Leif Can Do — End State

### A Task With No Intervention Required
```
Harry: "Add rate limiting to all my API endpoints"

Leif:
1. Maps the project → finds all 8 FastAPI endpoints
2. Fetches slowapi docs (the standard FastAPI rate limiter)
3. Writes the implementation matching Harry's existing code style
4. Runs it in sandbox → catches a config error
5. Debugger identifies the fix → resolves it
6. Runs again → all tests pass
7. Presents Harry with the complete, working implementation
8. Harry clicks Approve → files written to disk
```

### A Task That Needs Harry's Intelligence
```
Harry: "Should I use REST or GraphQL for the new client portal?"

Leif:
1. Recognises this is a strategic decision, not a coding task
2. Fetches current industry benchmarks and use case comparisons
3. Examines Harry's existing project structure
4. Presents a structured comparison with a recommendation
5. Escalates to Gemini 2.5 Flash for the depth of reasoning this deserves
6. Harry makes the call — Leif executes it
```

---

## The Build Phases

| Phase | What Gets Built | Result |
|---|---|---|
| **Current** | CLI + Web UI + Generative UI + Browser + Terminal + DOM | Leif as she is today |
| **Phase 4A** | Local LLM (Ollama + Phi-3 Mini) wired as Tier 0 | First free, offline responses |
| **Phase 4B** | Training data export from SQLite | Dataset ready for fine-tuning |
| **Phase 4C** | Colab Pro fine-tuning → GGUF download | Personalised local Leif |
| **Phase 5** | Web Retrieval API (DuckDuckGo, SO, GitHub, PyPI) | Live, accurate information |
| **Phase 6A** | Code Analyzer (pylint, ESLint) | Deterministic error detection |
| **Phase 6B** | Sandbox + Debugger (structured) | Code that verifies itself |
| **Phase 6C** | Project Structure Mapper | Full codebase awareness |
| **Phase 7** | ReAct Agent Loop + Agent Mode UI | Autonomous coding agent |
| **Phase 8** | ChromaDB Vector Memory | Long-term semantic recall |
| **Phase 9** | Full integration, tuning, hardening | Production-grade Leif |

---

## Honest Assessment — Where Leif Ends Up

### What Leif Will Be Excellent At
- Anything within Harry's established patterns and codebase → handles autonomously
- Debugging known error classes → instant, accurate, tool-verified
- Fetching and applying live documentation → no hallucination on known APIs
- Remembering everything Harry has ever told her → semantic memory
- Running offline for routine tasks → zero API cost

### What Leif Will Still Escalate
- Genuinely novel architectural problems Gemini handles better at depth
- Problems requiring real-world knowledge beyond the training cutoff
- Tasks requiring human judgment (business decisions, design choices)

### Where Leif Sits Relative to the Industry
| Product | Personalized to you | Runs offline | Knows your codebase | Autonomous loop | Free ongoing |
|---|---|---|---|---|---|
| GitHub Copilot | ❌ | ❌ | ⚠️ Limited | ❌ | ❌ |
| Cursor | ❌ | ❌ | ✅ | ⚠️ Limited | ❌ |
| ChatGPT | ⚠️ Limited | ❌ | ❌ | ❌ | ❌ |
| Devin | ❌ | ❌ | ⚠️ Per session | ✅ | ❌ ($500/month) |
| **Leif (full)** | **✅** | **✅** | **✅** | **✅** | **✅ mostly** |

---

## Technology Stack — Full Vision

| Layer | Technology |
|---|---|
| Brain Tier 0 | Phi-3 Mini 3.8B (fine-tuned, GGUF, Ollama) |
| Brain Tier 1 | Gemini 2.5 Flash + Thinking Mode |
| Brain Tier 2 | Gemini 2.5 Flash Lite |
| Brain Tier 3 | Groq Llama 3.3 70B |
| Fine-tuning | Unsloth + QLoRA on Colab Pro A100 |
| Web Retrieval | requests + trafilatura + BeautifulSoup (scratch-built) |
| Code Analysis | pylint + flake8 + mypy + ESLint + tsc |
| Sandbox | Python subprocess + structured output parser |
| Debugger | Custom stack trace parser + error classifier |
| Short Memory | SQLite (`D:\Leif_Data\leif_memory.db`) |
| Long Memory | ChromaDB (vector embeddings) |
| Project Index | Custom file tree + AST parser + Qwen2.5-Coder 1.5B (Summarizer) |
| Browser Agent | Playwright Chromium + browser_utils.py |
| Backend | Python 3.12 + FastAPI + Uvicorn |
| Frontend | React 19 + Vite + Vanilla CSS |
| Hardware | RTX 3050 (4GB VRAM) + i7 12th Gen + 16GB RAM |

---

*This is Leif. Built with intent by Harry.*
