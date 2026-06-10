# Phase 8: ReAct Agent Loop & Agent Mode UI

This phase connects all of our previously built tools (Web Search, Code Analyzer, Sandbox, and Codebase Intelligence) into an autonomous ReAct (Reason + Act) loop. We will also build the "Agent Mode" UI in the React frontend to display live thoughts and an approval gate for commands and file writes.

## User Review Required

> [!IMPORTANT]
> **Safety First:** The Agent will be able to write files and run terminal commands. To ensure safety, we are implementing an **Approval Gate Modal** in the UI. The Agent will explicitly pause and ask for your permission before executing any modifying commands or writing code to disk.

## Proposed Changes

### Backend (`leif/`)

#### [NEW] [agent.py](file:///c:/Users/Harriy/Desktop/project/Lief/leif/agent.py)
This module will contain the core ReAct loop:
- `agent_loop(task: str, ...)`: An asynchronous generator that yields steps.
- **THINK**: Uses the local `leif-local` fine-tuned model (or Gemini as a fallback) to decide the next action.
- **ACT**: Parses the thought and executes one of the available tools:
  - `web_retrieval`
  - `code_analyzer`
  - `sandbox_run`
  - `debugger`
  - `codebase_read`
  - `file_write` (Approval gated)
  - `terminal_run` (Approval gated)
- **OBSERVE**: Feeds the tool execution result back into the prompt for the next loop iteration.

#### [MODIFY] [api.py](file:///c:/Users/Harriy/Desktop/project/Lief/leif/api.py)
- Add a new streaming endpoint `POST /api/agent`
- This endpoint will stream Server-Sent Events (SSE) from the `agent_loop`, sending real-time `status` (e.g., "🧠 Thinking...", "🔧 Running code...") and `tool_calls` down to the frontend.

---

### Frontend (`frontend/src/`)

#### [MODIFY] [App.jsx](file:///c:/Users/Harriy/Desktop/project/Lief/frontend/src/App.jsx)
- **Agent Mode Toggle**: Add a switch to flip the UI between standard "Chat Mode" and the new "Agent Mode".
- **Live Feed**: Modify the message window to display streaming agent actions instead of just plain text.
- **Approval Flow**: When the SSE stream emits a `requires_approval` event, a modal will appear showing the proposed terminal command or file diff, prompting you to "Approve" or "Reject".

## Verification Plan

### Automated Tests
- No formal automated tests needed for the React UI.

### Manual Verification
1. Open the UI and switch on **Agent Mode**.
2. Give Leif a simple, multi-step task like: "Find out what the current python version is, and save it to a file called version.txt".
3. Verify the frontend live-updates with her thoughts ("Thinking...", "Running command python --version...").
4. Verify the **Approval Gate** correctly blocks the file write until you click "Approve".
