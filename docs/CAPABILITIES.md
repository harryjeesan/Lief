# 🌿 Leif — Complete Capability Analysis
*Last updated: June 2026*

---

## 1. What Leif Is

Leif is a **fully custom, personal AI assistant** built from scratch by Harry. She is not a wrapper around a chatbot API — she is a complete, full-stack agentic system with a custom personality, persistent memory, real-world system access, and a multi-tier AI brain.

She currently lives as a **React web app** (running locally at `localhost:5173`) powered by a **Python FastAPI backend** (`localhost:8000`). Conversations persist across sessions in a local SQLite database.

---

## 2. Architecture Overview

```
┌─────────────────────────────────┐
│        React Frontend           │  Vite + React 19
│  (Chat UI, Sidebar, Artifacts)  │  localhost:5173
└────────────────┬────────────────┘
                 │ HTTP / FormData
┌────────────────▼────────────────┐
│        FastAPI Backend          │  Python 3.12 + Uvicorn
│         leif/api.py             │  localhost:8000
└──────┬──────────────────────────┘
       │
  ┌────▼──────────────────────────┐
  │         AI Brain              │
  │  3-Tier Intelligence Router   │
  │  Tier 1: Gemini 2.5 Flash     │ ← Primary (Thinking Mode: 8192 budget)
  │  Tier 2: Gemini Flash Lite    │ ← Fallback (quota exceeded)
  │  Tier 3: Groq Llama 3.3 70B  │ ← Ultimate fallback (14,400 req/day free)
  └───────────────────────────────┘
       │
  ┌────▼──────────────────────────┐
  │       SQLite Database         │
  │    D:\Leif_Data\leif_memory.db│
  │  Conversations + Messages     │
  └───────────────────────────────┘
```

---

## 3. Current Capabilities

### 3.1 Core AI Chat
- **Conversational AI** powered by Google Gemini 2.5 Flash with Thinking Mode (8,192 token thinking budget per request)
- **Persistent memory:** Full conversation history stored in SQLite, loaded on every request — Leif remembers everything across sessions and page refreshes
- **Multi-conversation support:** ChatGPT-style sidebar with separate, named conversation threads
- **Auto-titling:** Conversations auto-named from the first user message
- **Context window:** Loads the full message history of the active conversation into context on each request

### 3.2 Personality & System Prompt
- **Custom engineered personality:** (`leif/system_prompt.py`) — warm, witty, direct, never sycophantic
- **Domain expertise:** Software & code, business strategy, calisthenics/fitness, emotional support
- **Teaching-first:** Explains WHY code works, never just hands over answers
- **Deep reasoning protocol:** Internal decompose → multi-angle → edge-case → verify pipeline runs silently before every response

### 3.3 3-Tier Intelligence Router
| Tier | Model | Trigger | Daily Limit |
|---|---|---|---|
| 1 | Gemini 2.5 Flash + Thinking | Primary | Key-dependent |
| 2 | Gemini 2.5 Flash Lite | 429 on Tier 1 | Key-dependent |
| 3 | Groq Llama 3.3 70B | All Gemini keys exhausted | 14,400 req/day |

### 3.4 API Key Rotation Pool
- Supports up to **3 Gemini API keys** in rotation
- Silent automatic failover when a key hits its quota limit
- Tracks exhaustion timestamps per key
- **Live Key Status Dashboard** in the UI showing real-time health per key, with reset countdowns

### 3.5 Groq Self-Reflection Loop
When Gemini is exhausted and Groq takes over, Leif runs a full **Drafter → Critic pipeline**:
1. Groq writes a draft response
2. Groq re-reads the draft as a critic, checks logic, style, persona alignment
3. Outputs the rewritten final response
This compensates for Groq's smaller intelligence gap vs. Gemini.

### 3.6 Generative UI — Artifact Engine
Leif can render **interactive React components** directly inside the chat stream using embedded JSON blocks. Current artifact types:

| Artifact Type | What It Renders |
|---|---|
| `action_list` | Clickable next-step buttons (clicking sends the action to Leif automatically) |
| `phase_grid` | Visual phase/roadmap cards with badges |
| `terminal_command` | Approval-gated terminal execution card |
| `browser_automation` | Approval-gated Playwright browser script card |

### 3.7 Terminal Tool (`/api/execute`)
- Leif can **propose and run PowerShell commands** on Harry's Windows machine
- **Security gate:** Commands only execute when Harry explicitly clicks "Approve & Run" in the UI
- Output is captured and fed back into Leif's context automatically for continued agentic workflow
- 15-second timeout prevents infinite hangs

### 3.8 Browser Subagent (`/api/browse`)
- Leif can write and execute **Playwright Chromium automation scripts**
- Launches a **visible browser** (headless=False) so Harry can watch in real time
- Script boilerplate injects `sys.path` with project root, allowing local module imports
- Also approval-gated: requires explicit user click to execute
- 45-second timeout, browser stays open 30 seconds after script for viewing
- Universal obstacle handler pattern for cookie banners, pop-ups, and ad skips

### 3.9 DOM Inspection (`leif/browser_utils.py`)
- `get_simplified_dom(page)` function available inside Playwright scripts
- Scans all visible interactive elements (buttons, inputs, links, selects, textareas)
- Maps tag name, text content, and key attributes (`id`, `name`, `placeholder`, `aria-label`, `role`, `href`, `type`)
- Output fed back to Leif for multi-step browser automation without guessing element selectors

### 3.10 File Attachment Support
- Users can attach files to any chat message
- **Images:** Sent as raw bytes with MIME type to Gemini's vision model
- **Text/Code files** (`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.json`, `.md`, `.csv`, `.txt`, `.pdf`): Decoded as UTF-8 and embedded in context (up to 15,000 chars)
- Attachment chip shown in UI, filename recorded in message history

---

## 4. Data Layer

### Database: SQLite (`D:\Leif_Data\leif_memory.db`)
Two tables:

**`conversations`**
```
id (UUID), title (TEXT), created_at, updated_at
```

**`messages`**
```
id (INT), conversation_id (FK), sender (TEXT), content (TEXT), timestamp
```

**Features:**
- Auto-migration: handles legacy schema without `conversation_id` column
- Auto-titling: first user message in each conversation becomes the title (truncated at 50 chars)
- Conversations ordered by most recent activity
- Full cascade delete (deleting conversation removes all messages)

---

## 5. Frontend UI Capabilities

- **Glassmorphic design** — neon gradients, blur effects, dark mode
- **Sidebar** — conversation list, create/delete conversations, toggle collapse
- **ReactMarkdown rendering** — full markdown in all chat messages
- **Generative UI rendering** — parses `json` code blocks and renders interactive components
- **File upload** — paperclip button, attachment chip, multi-type support
- **Typing indicator** — `...` shown while Leif is generating
- **Auto-scroll** — scrolls to latest message automatically
- **Key Status Panel** — live API key health dashboard at top of chat
- **Leif avatar** — custom sci-fi avatar with green status dot indicator
- **Mobile-responsive toggle** — sidebar collapse button for smaller viewports

---

## 6. Backend API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/chat` | Main chat endpoint (FormData: message, conversation_id, optional file) |
| `GET` | `/api/conversations` | List all conversations |
| `POST` | `/api/conversations` | Create a new conversation |
| `DELETE` | `/api/conversations/{id}` | Delete conversation + all messages |
| `GET` | `/api/conversations/{id}/messages` | Load messages for a conversation |
| `POST` | `/api/execute` | Run a terminal command (security-gated) |
| `POST` | `/api/browse` | Run a Playwright browser script (approval-gated) |
| `GET` | `/api/key-status` | Live status of all API keys in rotation pool |

---

## 7. Known Limitations

| Limitation | Detail |
|---|---|
| **API quota burns fast** | Thinking Mode (8,192 budget) on every message, including simple ones |
| **No web search** | Leif cannot search the internet autonomously — only via approval-gated Browser Subagent |
| **No streaming** | Responses sent as single payload, no token-by-token streaming |
| **No voice** | No TTS/STT integration |
| **No local LLM** | All AI inference goes through external APIs — no offline capability |
| **No vector memory** | SQLite only, no semantic search over past conversations |
| **Browser requires approval** | Every browser action needs Harry's explicit click — not autonomous |
| **Windows encoding dependency** | Requires `PYTHONIOENCODING=utf-8` to handle emoji in print statements |

---

## 8. Phase Completion Status

| Phase | Status | Description |
|---|---|---|
| Phase 1 | ✅ Complete | CLI chat, Gemini integration, personality, UTF-8 fix |
| Phase 2 | ✅ Complete | FastAPI backend, SQLite memory, React UI, CORS |
| Phase 3 | ✅ Complete | Generative UI, terminal tool, browser subagent, key rotation, Groq fallback |
| Phase 3.5 | ✅ Complete | DOM inspection, sys.path injection, file attachments, multi-conversation |

---

## 9. Planned Roadmap (Phase 4+)

| Feature | Priority | Notes |
|---|---|---|
| **Autonomous Web Search** | High | Enable Gemini's native Google Search tool — one line change |
| **REFLECTION_MODE toggle** | High | On/off flag to conserve API quota on simple messages |
| **Local LLM (Ollama)** | High | Tier 0 router — Phi-3 Mini or Qwen2.5 7B locally via Ollama |
| **Fine-tuned local model** | Medium | Train on `leif_memory.db` via Colab Pro A100, export GGUF, run on RTX 3050 |
| **Vector Memory (ChromaDB)** | Medium | Replace SQLite full-text with semantic search across all conversations |
| **Response Streaming** | Medium | Token-by-token output for better UX |
| **`pyautogui` Mouse Agent** | Low | Physical cursor control for apps without APIs |
| **Voice Integration** | Low | TTS/STT for hands-free conversational mode |
| **Dashboard Control Panel** | Low | Settings, metrics, tool monitoring in-chat |

---

## 10. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| AI Engine | Google Gemini 2.5 Flash | Primary |
| AI Fallback | Gemini 2.5 Flash Lite | Tier 2 |
| AI Ultimate Fallback | Groq Llama 3.3 70B | Tier 3 |
| Backend Framework | FastAPI + Uvicorn | Python 3.12 |
| Memory | SQLite via custom `database.py` | D:\Leif_Data\ |
| Frontend | React 19 + Vite | v8 |
| Markdown | react-markdown | v10 |
| Browser Agent | Playwright (Chromium) | Sync API |
| Environment | python-dotenv | Isolated venv |
| DOM Inspection | Custom `browser_utils.py` | Leif-native |

---

*Built with intent by Harry.*
