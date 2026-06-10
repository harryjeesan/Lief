# Upgrade Leif to the 4-Tier Multi-Agent MoE Architecture

This is the actionable, step-by-step master plan to physically build the Architecture we designed today. We will transform Leif from a single-model orchestrator into a Multi-Agent ecosystem.

## User Review Required
> [!IMPORTANT]
> Please review this roadmap before we begin tomorrow. This will require downloading massive AI models (approx 4GB-8GB each) to your hard drive. Ensure you have at least 20GB of free disk space before we start!

## Open Questions
> [!WARNING]
> 1. Which local "Expert" models do you want to download? (I recommend `llama3` for Copywriting and `deepseek-coder` for Web Development, but we can choose others).
> 2. Do you have an active OpenAI/Anthropic API key to configure the Tier 3 (GPT-4o/Claude) Master Review tool? If not, we can build the tool now and activate it later.

---

## Proposed Changes

### Phase 1: Model Acquisition & Ollama Setup
Before modifying code, we need to populate your "Local Agency" with experts.
- Run terminal commands to pull the necessary models:
  - `ollama pull llama3` (The Local Copywriter)
  - `ollama pull deepseek-coder` (The Local Web Dev)
- Verify Ollama's memory management settings to ensure it seamlessly swaps models in and out of VRAM without crashing.

---

### Phase 2: Python Backend Expansion (leif/agent.py & leif.api)
We need to extend the backend to handle the new MoE workflow.

#### [MODIFY] leif/routers/agent_api.py
- Add new REST endpoints to handle the specific expert calls:
  - `POST /api/consult_copywriter` -> Triggers Ollama `llama3`.
  - `POST /api/consult_webdev` -> Triggers Ollama `deepseek-coder`.
  - `POST /api/review_content` -> Triggers Tier 2 (Copilot).
  - `POST /api/master_review` -> Triggers Tier 3 (GPT-4o).

---

### Phase 3: VS Code Extension Upgrades
We must give Leif (The Orchestrator) the "tools" to command these new experts.

#### [MODIFY] leif-vscode/src/extension.ts
- **System Prompt Updates:** Add the new tools to Leif's system prompt instructions.
- **Tool Handlers:** Add the execution logic for the new tools.
  - `ask_local_copywriter`: Fetches from `llama3` and saves to `.draft_buffer.txt`.
  - `ask_local_web_dev`: Fetches from `deepseek-coder` and saves to `.code_buffer.txt`.
  - `review_premium_content`: Fetches from Copilot and saves to `.premium_buffer.txt`.
  - `master_review_content`: Fetches from GPT-4o and saves to `.master_buffer.txt`.

---

## Verification Plan

### Manual Verification
Tomorrow, once the architecture is built, we will run the ultimate stress test.
- **The Prompt:** *"Leif, build an Upwork Proposal for a React Development job."*
- **The Expected Flow:** 
  1. We will watch the terminal to confirm Ollama puts Leif to sleep and wakes up `llama3` to draft the proposal.
  2. We will watch Leif pass the draft to Copilot for review.
  3. We will watch Leif pass the polished text to Tier 3.
  4. We will review the final `proposal.md` to guarantee it is world-class.
