# 🌿 Leif — Personal AI Assistant

Leif is a custom-built, highly personalized AI assistant designed from scratch. She acts as a pair programmer, business strategist, and fitness coach — powered by a full agentic architecture with Generative UI, system tool access, a visual Browser Subagent, Local LLM integration, and a dedicated VS Code extension.

## ✅ Phase 1 — CLI Foundation
- **Custom Personality:** Witty, direct, and genuinely supportive.
- **Teaching-First Code Assistance:** Explains concepts line-by-line.
- **Stateful Memory:** Maintains conversational context.

## ✅ Phase 2 — Web UI & Persistent Memory
- **FastAPI Backend:** REST API powering chat and history endpoints.
- **SQLite Persistence:** Full conversation history saved across sessions.
- **React Frontend:** Premium glassmorphic chat UI with avatar.

## ✅ Phase 3 — Generative UI & Agentic Tools
- **Generative Artifacts Engine:** Interactive React components directly inside the chat.
- **Security Gate Architecture:** Approvals required for terminal and browser execution.
- **Terminal & Browser Subagents:** Playwright-powered visual Chromium automation and PowerShell execution.

## ✅ Phase 4-7 — Local AI, Intelligence & IDE Integration
- **Local LLM Engine:** Native integration with local models (e.g., `qwen2.5-coder`) using Ollama, dramatically reducing API costs.
- **Auto-Trainer & Data Export:** Automated pipelines (`scripts/auto_trainer.py`) to export memory and fine-tune models to mirror your personal coding style.
- **Codebase Intelligence System:** A 3-tool pipeline (`codebase_reader.py`, `codebase_summarizer.py`, `codebase_compiler.py`) to parse, summarize, and compress massive repositories into lightweight intelligence reports.
- **VS Code Extension (`leif-vscode`):** A dedicated, native IDE extension bringing Leif's Agent Mode directly into your editor's sidebar.

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| **AI Engine** | Google Gemini (Primary) + Local Ollama / Qwen (Offline/Summaries) |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Memory & Storage** | SQLite (Memory), ChromaDB (Planned Vectors) |
| **Frontend & IDE** | React 19, Vite, Vanilla CSS, VS Code Extension API |
| **Agent Tools** | Playwright (Browser), AST / Esprima (Code Parsing) |

## 📂 Project Documentation
For technical walkthroughs and dev logs, check out the [docs](./docs) folder:
* [**Build Plan**](./docs/BUILD_PLAN.md) — The complete phase-by-phase roadmap.
* [**Phase 7 Plan**](./docs/PHASE_7_PLAN.md) — The Codebase Intelligence Sub-System architecture.
* [**Vision Document**](./docs/VISION.md) — The full architectural vision.
* [**Auto Trainer Guide**](./docs/AUTO_TRAINER_GUIDE.md) — How to export and fine-tune models.
* [Capabilities Analysis](./docs/CAPABILITIES.md) — Breakdown of features and limitations.

## 🔒 Proprietary Software
This repository is public for **portfolio and evaluation purposes only**. The source code is proprietary.
- You may **not** clone, download, modify, run, or distribute this code.
- Please refer to the `LICENSE` file for full terms and conditions.

## 🔮 Future Roadmap
- [ ] `pyautogui` Mouse Agent — physical cursor control for apps without APIs
- [ ] Voice Integration (TTS/STT) — fully hands-free conversational mode
- [ ] Vector Memory (Phase 9) — upgrade to ChromaDB for semantic long-term recall
- [ ] Advanced ReAct Agent Loop — verified reason + act loop in a sandbox

---
*Built with intent by Harry.*
