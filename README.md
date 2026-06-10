# 🌿 Leif — Personal AI Assistant

Leif is a custom-built, highly personalized AI assistant designed from scratch. She acts as a pair programmer, business strategist, and fitness coach — powered by a full agentic architecture with Generative UI, system tool access, and a visual Browser Subagent.

## ✅ Phase 1 — CLI Foundation
- **Custom Personality:** Witty, direct, and genuinely supportive — built to feel like a sharp co-founder, not a robotic assistant.
- **Teaching-First Code Assistance:** Explains concepts line-by-line to build real development skills.
- **Stateful Memory:** Maintains conversational context throughout the active session.
- **Graceful Error Handling:** Custom catching for rate limits, API timeouts, and missing credentials.

## ✅ Phase 2 — Web UI & Persistent Memory
- **FastAPI Backend:** REST API powering `/api/chat` and `/api/history` endpoints.
- **SQLite Persistence:** Full conversation history saved across sessions. Loads instantly on page refresh.
- **React Frontend:** Premium glassmorphic chat UI with avatar, typing indicators, and auto-scroll.
- **Agentic Self-Reflection Loop:** Every response goes through a Drafter → Critic pipeline, massively elevating response quality without fine-tuning.

## ✅ Phase 3 — Generative UI & Agentic Tools
- **Generative Artifacts Engine:** Leif renders interactive React components (Action Lists, Phase Grids) directly inside the chat stream — no plain text walls.
- **Security Gate Architecture:** Leif can propose terminal commands and browser scripts, but they **do not execute** until Harry explicitly clicks "Approve & Run" in the UI.
- **Terminal Tool (`/api/execute`):** Leif can run PowerShell commands on Harry's Windows machine and read back the output to continue the workflow.
- **Browser Subagent (`/api/browse`):** Playwright-powered visual Chromium automation. Leif can navigate websites, search YouTube, skip ads, and dismiss cookie banners on any site.
- **API Key Rotation Pool:** Supports up to 3 Gemini API keys with automatic silent failover on quota exhaustion.
- **Live Key Status Dashboard:** React panel showing each key's health (active/exhausted/standby) with real-time reset countdowns.

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| **AI Engine** | Google Gemini 2.5 Flash (Primary) + Flash Lite (Fallback) |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Memory** | SQLite (via custom `database.py`) |
| **Frontend** | React 19, Vite, Vanilla CSS |
| **Browser Agent** | Playwright (Chromium) |
| **Environment** | `python-dotenv`, isolated `venv` |

## 📂 Project Documentation
For technical walkthroughs and dev logs, check out the [docs](./docs) folder:
* [**Build Plan**](./docs/BUILD_PLAN.md) — The complete 10-phase plan to build future Leif — local LLM, fine-tuning, web retrieval, sandbox, agent loop, and vector memory.
* [**Vision Document**](./docs/VISION.md) — The complete architecture of what Leif becomes — full agent loop, local LLM, tool suite, web retrieval.
* [Capabilities Analysis](./docs/CAPABILITIES.md) — Full breakdown of every current feature, endpoint, limitation, and roadmap.
* [Development Log](./docs/DEVELOPMENT_LOG.md) — Step-by-step history of milestones and setup.
* [DOM Inspection Walkthrough](./docs/WALKTHROUGH.md) — Walkthrough of the browser subagent element extraction upgrade.

## 🔒 Proprietary Software
This repository is public for **portfolio and evaluation purposes only**. The source code is proprietary.
- You may **not** clone, download, modify, run, or distribute this code.
- Please refer to the `LICENSE` file for full terms and conditions.

## 🔮 Phase 4 Roadmap
- [ ] `pyautogui` Mouse Agent — physical cursor control for apps without APIs
- [ ] Voice Integration (TTS/STT) — fully hands-free conversational mode
- [ ] Self-Reflection toggle — `REFLECTION_MODE=off` flag to conserve API quota
- [ ] Vector Memory — upgrade SQLite to ChromaDB for semantic long-term recall
- [ ] Dashboard Control Panel — settings, metrics, and tool monitoring in-chat

---
*Built with intent by Harry.*
