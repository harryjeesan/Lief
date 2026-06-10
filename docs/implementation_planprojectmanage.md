# [Goal Description]

Build a **Project Manager Sub-System** into Leif's core engine. When given a massive Upwork prompt (e.g., "Build a full stack Next.js app with a dashboard, auth, and database"), a single agent loop might run out of context or get confused. The Project Manager will automatically break massive tasks into 3-7 sequential milestones and execute them one by one, ensuring she never gets overwhelmed.

## User Review Required

> [!IMPORTANT]
> The Project Manager will act as an orchestrator. It will ask Groq/Gemini to write out a project plan, and then it will spin up a fresh instance of Leif's `agent_loop` for each milestone. This means she will execute 50 iterations *per milestone*, essentially giving her infinite runway to build massive applications!

## Proposed Changes

### `leif/api.py`

- **[MODIFY] `start_agent_loop`**
  - Add support for the `/project ` command.
  - If a user types `/project [task]`, route the execution to a new function: `project_manager_loop`.

### `leif/agent.py`

- **[NEW] `project_manager_loop(task: str)`**
  - **Step 1 (Planning)**: Make a strict JSON API call to Groq/Gemini asking it to act as a Senior Architect. It will break the user's `task` into a JSON array of 3-7 sequential milestones.
  - **Step 2 (Execution)**: Loop through the milestones. For each milestone, dynamically yield the execution stream from `agent_loop()`.
  - **Context Chaining**: Feed the previous milestones into the next milestone's prompt (e.g., `"Context: You just completed Milestone 1. Now begin Milestone 2: ..."`) so she maintains perfect continuity.

## Verification Plan

### Manual Verification
- Start an Agent Mode session and type: `"/project Build a complete React tic-tac-toe game with a score tracker, restart button, and styling."`
- Verify that she announces her milestones in the UI and executes them sequentially.
