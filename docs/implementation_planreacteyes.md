# Upgrade VS Code Agent Permissions

The current VS Code Native Language Model (and the backend model when it was running) gets stuck in loops because it is "blind". It can type commands into the terminal, but it cannot read what the terminal prints out. It also cannot read or write files directly from the editor to see if its changes worked.

To solve this, we will upgrade the VS Code Extension (`leif-vscode/src/extension.ts`) to give the Agent full autonomous permissions to the terminal and editor.

## User Review Required

> [!WARNING]
> This upgrade will give the autonomous agent loop (and the VS Code Native AI) the ability to run shell commands in the background and read/write files directly on your machine. This is very powerful, but you must monitor what the AI decides to run!

## Proposed Changes

### leif-vscode/src/extension.ts

#### [MODIFY] [extension.ts](file:///c:/Users/Harriy/Desktop/project/Lief/leif-vscode/src/extension.ts)
1. **Import Required Modules**: Import `child_process`, `util`, `fs/promises`, and `path` at the top of the file.
2. **Update System Prompt**: Add documentation for three new tools:
   - `terminal_run` (will now be documented as returning terminal output).
   - `editor_read` - args: `{"path": "..."}`.
   - `editor_write` - args: `{"path": "...", "content": "..."}`.
3. **Upgrade `terminal_run` Tool**: Replace `vscode.window.terminals...sendText()` with `child_process.exec`. Capture `stdout` and `stderr` and inject it back into the agent's `history` context (truncated to prevent context window blowouts).
4. **Implement `editor_read` Tool**: Use `fs.readFile` to read files relative to the workspace root and inject the contents into the agent's `history`.
5. **Implement `editor_write` Tool**: Use `fs.writeFile` to allow the agent to write code autonomously.

## Verification Plan
1. Edit `extension.ts` with the new tools.
2. Recompile the extension using `npm run compile` (or `tsc`).
3. Have you run the extension again to verify that the Native AI successfully reads a file and returns its contents, ending the blind repeating loop.
