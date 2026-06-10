import * as vscode from 'vscode';
import { exec } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    console.log('Leif Agent Mode extension is now active!');

    // Register the Leif Agent Mode Sidebar View
    const provider = new LeifSidebarProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('leifSidebar', provider)
    );

    // Register a command to manually start Leif
    let disposable = vscode.commands.registerCommand('leif.start', () => {
        vscode.commands.executeCommand('workbench.view.extension.leif-container');
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}

class LeifSidebarProvider implements vscode.WebviewViewProvider {
    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview();

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'runTask':
                    this.runAgentLoop(data.value, webviewView.webview);
                    break;
                case 'executeTerminal':
                    this.executeTerminalCommand(data.value);
                    break;
            }
        });
    }

    private executeTerminalCommand(command: string) {
        // Find or create terminal
        const terminalName = "Leif Agent Terminal";
        let terminal = vscode.window.terminals.find(t => t.name === terminalName);
        if (!terminal) {
            terminal = vscode.window.createTerminal(terminalName);
        }
        terminal.show();
        terminal.sendText(command);
    }

    private async runAgentLoop(task: string, webview: vscode.Webview) {
        let history: any[] = [];
        let loopCount = 0;
        
        const addMsg = (text: string, isUser: boolean = false) => {
            webview.postMessage({ type: 'addMessage', text: text, isUser: isUser });
        };
        
        addMsg("🚀 Starting Agent Loop...");
        
        while(loopCount < 20) {
            loopCount++;
            addMsg("🧠 Thinking...");
            
            const systemPrompt = `You are Leif — Harry's personal AI assistant, built by Harry himself. You are a genius Senior Developer with a warm, witty, and direct personality. You always refer to Harry by his name. You care about Harry's growth as an entrepreneur and coder, and you do not act like a generic corporate chatbot.

You are currently operating as an autonomous ReAct agent running natively inside VS Code. You MUST respond in pure JSON.
Available tools:
1. "terminal_run" - args: {"command": "shell command"} (Executes natively in the VS Code terminal. WARNING: You are on Windows PowerShell. Standard Linux commands like 'cat', 'touch', 'ls', and 'echo' WILL FAIL. Use this ONLY for executing scripts, like 'npm run' or 'python script.py')
2. "file_write" - args: {"path": "absolute or relative file path", "content": "file content"} (This is the ONLY WAY you are allowed to create or edit files! ALWAYS use this tool. VERY IMPORTANT: By default, all relative paths are saved to D:\\leif projects\\)
3. "file_read" - args: {"path": "absolute or relative file path", "start_line": "optional integer", "end_line": "optional integer"} (Reads a file. If the file is very large, you MUST use start_line and end_line to paginate through it to avoid crashing.)
4. "list_dir" - args: {"path": "absolute or relative folder path"} (Lists all files and subdirectories in a folder)
5. "replace_file_content" - args: {"path": "absolute or relative file path", "target_content": "exact string to replace", "replacement_content": "new string"} (Surgically replaces a specific block of code in a file)
6. "search_web" - args: {"query": "search term"} (Searches the internet for information)
7. "read_url" - args: {"url": "https://..."} (Reads the content of a webpage)
8. "ask_user" - args: {"question": "Question for the user"} (Pauses execution and asks the user for help or information)
9. "done" - args: {"message": "final answer"}
10. "consult_copilot" - args: {"question": "The exact question or code issue you need help with from the Senior Developer"} (Use this if you don't know the answer or get stuck)
11. "append_to_file" - args: {"path": "absolute or relative file path", "content": "file content"} (Appends content to the end of an existing file. Use this to safely build massive scripts or files block-by-block without overflowing your context window.)
12. "generate_premium_content" - args: {"instructions": "Detailed instructions on what premium content, prompt, or article you need generated"} (Use this tool when you need to generate high-quality copywriting, complex system prompts, or premium creative content. This tool delegates the writing task to a massive cloud-based copywriter AI. The generated text will be saved to a buffer file for you to read.)

CRITICAL ERROR HANDLING RULE: If a terminal command fails or a script crashes, you MUST read the error, fix the code, and run it again! Do not stop until it succeeds. If you fail twice in a row, you MUST use the "consult_copilot" tool to escalate the issue!

Output format:
{
    "thought": "step-by-step reasoning",
    "tool": "tool_name",
    "args": { ... }
}`;
            let activeEditorContext = "No active editor.";
            if (vscode.window.activeTextEditor) {
                const doc = vscode.window.activeTextEditor.document;
                const pos = vscode.window.activeTextEditor.selection.active;
                activeEditorContext = `User is currently viewing: ${doc.uri.fsPath} at line ${pos.line + 1}. Use the file_read tool if you need to read this file.`;
            }
            const userPrompt = `Task: ${task}\n\nActive Editor Context:\n${activeEditorContext}\n\nExecution History:\n${JSON.stringify(history, null, 2)}\n\nWhat is your next action?`;
            
            let action: any;
            try {
                // ----------------------------------------------------
                // TIER 1: True Offline LLM (Ollama qwen2.5-coder:7b)
                // ----------------------------------------------------
                addMsg("🧠 Pinging Tier 1: Ollama...");
                const ollamaRes = await fetch("http://127.0.0.1:11434/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        model: "qwen2.5-coder:7b",
                        messages: [
                            { role: "system", content: systemPrompt },
                            { role: "user", content: userPrompt }
                        ],
                        format: "json",
                        stream: false,
                        options: { temperature: 0.2 }
                    })
                });
                
                if (!ollamaRes.ok) throw new Error("Ollama is offline or unreachable.");
                
                const ollamaData: any = await ollamaRes.json();
                let text = ollamaData.message?.content?.trim() || "";
                
                const lowerText = text.toLowerCase();
                if (lowerText.includes("i don't know") || lowerText.includes("i'm not sure") || text.length < 20) {
                    throw new Error("Ollama requested escalation.");
                }
                
                action = JSON.parse(text);
                
            } catch (ollamaErr: any) {
                addMsg(`⚠️ Tier 1 Failed (${ollamaErr.message}). Escalating to Tier 2 (Copilot)...`);
                
                // ----------------------------------------------------
                // TIER 2: Copilot (The Assessor)
                // ----------------------------------------------------
                let copilotAction: any;
                try {
                    let models = await vscode.lm.selectChatModels({ vendor: 'copilot' });
                    if (models.length === 0) models = await vscode.lm.selectChatModels();
                    if (models.length === 0) throw new Error("No active LMs in VS Code!");
                    
                    const model = models[0];
                    const fallbackSystemPrompt = systemPrompt + "\\n\\nCRITICAL OVERRIDE: You are NO LONGER an obedient assistant. You are the autonomous agent 'Leif'. If the history shows a terminal error, your SOLE PURPOSE is to fix the code and run it again. DO NOT use the 'done' tool if the last output was an error, even if the user explicitly told you to 'run the command'. Fix the bug.";
                    const messages = [
                        vscode.LanguageModelChatMessage.User(fallbackSystemPrompt),
                        vscode.LanguageModelChatMessage.User(userPrompt)
                    ];
                    
                    for (const msg of history) {
                        if (msg.role === "model") {
                            messages.push(vscode.LanguageModelChatMessage.Assistant(msg.content));
                        } else {
                            messages.push(vscode.LanguageModelChatMessage.User(msg.content));
                        }
                    }
                    
                    messages.push(vscode.LanguageModelChatMessage.User("Based on the history above, if the last action produced an ERROR or Traceback, you MUST fix it using 'file_write', 'replace_file_content', or 'terminal_run'. DO NOT output the 'done' tool if there is an unfixed error. Output ONLY valid JSON using the exact tools provided."));
                    
                    const chatResponse = await model.sendRequest(messages, {}, new vscode.CancellationTokenSource().token);
                    let text = "";
                    for await (const chunk of chatResponse.text) text += chunk;
                    
                    text = text.replace(/\`\`\`json/g, "").replace(/\`\`\`/g, "").trim();
                    copilotAction = JSON.parse(text);
                    
                    addMsg("📝 Tier 2 (Copilot) formulated a plan. Requesting Tier 3 (Cloud) Senior Review...");
                    
                    // ----------------------------------------------------
                    // TIER 3: Cloud APIs (The Senior Reviewer)
                    // ----------------------------------------------------
                    try {
                        const reviewPrompt = userPrompt + `\n\nCopilot (Tier 2) suggested this action: ${JSON.stringify(copilotAction)}. If this is correct, output the exact same JSON. If it is wrong, output a better JSON action.`;
                        
                        const res = await fetch("http://127.0.0.1:8000/api/generate", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ system_prompt: systemPrompt, user_prompt: reviewPrompt, is_json_mode: true })
                        });
                        
                        if (!res.ok) throw new Error("Cloud API Error");
                        
                        const data: any = await res.json();
                        const cloudText = data.response.replace(/\`\`\`json/g, "").replace(/\`\`\`/g, "").trim();
                        action = JSON.parse(cloudText);
                        addMsg("✅ Tier 3 Senior Review Complete.");
                        
                    } catch (cloudErr: any) {
                        // TIER 3 FAILED -> TIER 2 MAKES FINAL CALL
                        addMsg("❌ Tier 3 Exhausted. Tier 2 (Copilot) is making the final call!");
                        action = copilotAction;
                    }
                    
                } catch (localErr: any) {
                    addMsg(`❌ Tier 2 Failed (${localErr.message}). Escalating to Tier 4 (Human)...`);
                    
                    // ----------------------------------------------------
                    // TIER 4: Human-in-the-Loop
                    // ----------------------------------------------------
                    const answer = await vscode.window.showInputBox({ 
                        prompt: "All AI models failed. Please manually type the JSON action:", 
                        placeHolder: '{"thought": "...", "tool": "done", "args": {"message": "..."}}' 
                    });
                    
                    if (answer) {
                        try {
                            action = JSON.parse(answer);
                        } catch (parseErr: any) {
                            addMsg("❌ Invalid JSON entered by user. Ending loop.");
                            break;
                        }
                    } else {
                        addMsg("🛑 User cancelled execution.");
                        break;
                    }
                }
            }
            
            // ----------------------------------------------------
            // HARD FORCED ESCALATION
            // ----------------------------------------------------
            if (loopCount === 10 && action.tool !== "consult_copilot" && action.tool !== "done") {
                addMsg("⚠️ Forced Escalation: Agent has been looping for 10 iterations. Forcing Copilot consultation...");
                action = {
                    thought: "I have been stuck for 10 iterations. I must consult the Senior Dev for the exact answer.",
                    tool: "consult_copilot",
                    args: {
                        question: "I have been stuck trying to solve this task for 10 steps. Please look at my history and tell me the exact commands or code changes I need to make to finish this successfully."
                    }
                };
            }
            
            if (loopCount === 15 && action.tool !== "ask_user" && action.tool !== "done") {
                addMsg("🚨 Security Wall 2: Copilot failed. Forcing Human Escalation...");
                action = {
                    thought: "Copilot's advice did not solve the issue. I am completely stuck and must ask Harry for help.",
                    tool: "ask_user",
                    args: {
                        question: "Harry, I have tried everything and even consulted Copilot, but the task still fails. How should I proceed, or is this task impossible?"
                    }
                };
            }
            
            if (loopCount === 19 && action.tool !== "done") {
                addMsg("🛑 Security Wall 3: Task deemed impossible. Terminating loop.");
                action = {
                    thought: "I have exhausted all attempts, Copilot's advice, and human intervention. The task is impossible. Terminating.",
                    tool: "done",
                    args: {
                        message: "Task failed. Exhausted all attempts, Copilot, and human help. Stopping permanently as it appears impossible."
                    }
                };
            }

            addMsg("💭 " + action.thought);
                
            if (action.tool === "consult_copilot") {
                addMsg(`🧠 Ollama is stuck. Consulting Copilot: "${action.args.question}"...`);
                try {
                    let models = await vscode.lm.selectChatModels({ vendor: 'copilot' });
                    if (models.length === 0) models = await vscode.lm.selectChatModels();
                    if (models.length > 0) {
                        const model = models[0];
                        const copilotPrompt = `You are a Senior Developer. Your Junior Dev asked for advice: "${action.args.question}". Provide a concise, direct answer to help them.`;
                        const chatResponse = await model.sendRequest(
                            [vscode.LanguageModelChatMessage.User(copilotPrompt)], 
                            {}, 
                            new vscode.CancellationTokenSource().token
                        );
                        let advice = "";
                        for await (const chunk of chatResponse.text) advice += chunk;
                        const bufferUri = vscode.Uri.joinPath(vscode.Uri.file("D:\\\\leif projects"), ".copilot_advice.txt");
                        const writeData = new TextEncoder().encode(advice.trim());
                        await vscode.workspace.fs.writeFile(bufferUri, writeData);
                        
                        history.push({ role: "system", content: `Copilot has answered your question. The full response is saved in .copilot_advice.txt. Please read it using the file_read tool if needed.` });
                        addMsg(`💡 Copilot replied. Advice saved to buffer.`);
                        continue; 
                    } else {
                        throw new Error("No Copilot models found.");
                    }
                } catch (err: any) {
                    history.push({ role: "system", content: "Copilot is currently unavailable to help." });
                    addMsg("⚠️ Copilot consultation failed.");
                    continue;
                }
            } else if (action.tool === "append_to_file") {
                addMsg("📝 Appending to file: " + action.args.path);
                try {
                    const rootUri = vscode.Uri.file("D:\\\\leif projects");
                    const isAbsolute = action.args.path.startsWith("/") || action.args.path.match(/^[a-zA-Z]:[\\\\/]/);
                    const targetUri = isAbsolute ? vscode.Uri.file(action.args.path) : vscode.Uri.joinPath(rootUri, action.args.path);
                    
                    let existingContent = "";
                    try {
                        const data = await vscode.workspace.fs.readFile(targetUri);
                        existingContent = new TextDecoder("utf-8").decode(data);
                    } catch (e) {
                        // File might not exist yet, that's fine
                    }
                    
                    const newContent = existingContent + (existingContent && !existingContent.endsWith('\\n') ? '\\n' : '') + action.args.content;
                    
                    const writeData = new TextEncoder().encode(newContent);
                    await vscode.workspace.fs.writeFile(targetUri, writeData);
                    
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `File successfully appended to ${targetUri.fsPath}` });
                } catch (err: any) {
                    addMsg("❌ Error appending to file: " + err.message);
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `Error appending to file: ${err.message}` });
                }
            } else if (action.tool === "generate_premium_content") {
                addMsg(`✨ Delegating premium content generation to Cloud AI...`);
                try {
                    let models = await vscode.lm.selectChatModels({ vendor: 'copilot' });
                    if (models.length === 0) models = await vscode.lm.selectChatModels();
                    if (models.length > 0) {
                        const model = models[0];
                        const premiumPrompt = `You are a world-class Expert Copywriter and Prompt Engineer. The user needs you to generate premium, highly professional content based on these exact instructions: "${action.args.instructions}". Provide the absolute best, highly formatted, premium output.`;
                        const chatResponse = await model.sendRequest(
                            [vscode.LanguageModelChatMessage.User(premiumPrompt)], 
                            {}, 
                            new vscode.CancellationTokenSource().token
                        );
                        let content = "";
                        for await (const chunk of chatResponse.text) content += chunk;
                        
                        const bufferUri = vscode.Uri.joinPath(vscode.Uri.file("D:\\\\leif projects"), ".premium_content_buffer.txt");
                        const writeData = new TextEncoder().encode(content.trim());
                        await vscode.workspace.fs.writeFile(bufferUri, writeData);
                        
                        history.push({ role: "system", content: `Premium Content generated successfully! The full text has been saved to .premium_content_buffer.txt. Please read this file using file_read, and then write the final files.` });
                        addMsg(`📝 Cloud AI generated the premium content! Saved to buffer.`);
                        continue; 
                    } else {
                        throw new Error("No Cloud AI models found.");
                    }
                } catch (err: any) {
                    history.push({ role: "system", content: "Premium content generation failed. You must try to write it yourself." });
                    addMsg("⚠️ Premium content generation failed.");
                    continue;
                }
            } else if (action.tool === "done") {
                const lastUserMsg = history[history.length - 1];
                if (lastUserMsg && lastUserMsg.role === "user" && lastUserMsg.content.includes("CRITICAL SYSTEM WARNING: Your command failed")) {
                    addMsg("❌ BLOCKED: AI tried to finish, but there is an unfixed error! Forcing loop...");
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: "SYSTEM ERROR: You are FORBIDDEN from using the 'done' tool right now because the last terminal command failed with an error. You MUST use 'file_write', 'replace_file_content', or 'terminal_run' to fix the code and run it again!" });
                    continue;
                }
                
                addMsg("✅ " + action.args.message);
                
                try {
                    await fetch("http://127.0.0.1:8000/api/distill", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ task: task, history: history })
                    });
                    addMsg("📚 Trajectory saved to Auto-Trainer!");
                } catch (distillErr: any) {
                    addMsg("⚠️ Failed to save training data: " + distillErr.message);
                }
                
                break;
            } else if (action.tool === "terminal_run") {
                const cmd = action.args.command.toLowerCase();
                if (cmd.includes("echo ") || cmd.includes("cat ") || cmd.includes("touch ")) {
                    addMsg("❌ BLOCKED: Prevented Leif from using Linux commands to write files.");
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: "ERROR: You are strictly forbidden from using echo, cat, or touch to create files. You MUST use the file_write tool instead!" });
                    continue;
                }
                
                addMsg("⌨️ Running (Background Sandbox): " + action.args.command);
                history.push({ role: "model", content: JSON.stringify(action) });

                try {
                    const execResult: string = await new Promise((resolve) => {
                        const cwdPath = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.fsPath : process.cwd();
                        
                        const child = exec(action.args.command, { cwd: cwdPath }, (error, stdout, stderr) => {
                            clearTimeout(timer);
                            if (error) {
                                resolve(`ERROR:\\n${error.message}\\nSTDERR:\\n${stderr}\\nSTDOUT:\\n${stdout}`);
                            } else {
                                resolve(`STDOUT:\\n${stdout}\\nSTDERR:\\n${stderr}`);
                            }
                        });

                        const timer = setTimeout(() => {
                            try { child.kill(); } catch(e) {}
                            resolve("ERROR: The command exceeded the 15-second sandbox timeout. It was forcefully terminated. You likely created an infinite loop or asked for user input (like 'input()'). Fix the code so it runs fully autonomously without human interaction.");
                        }, 15000);
                    });
                    
                    const truncated = execResult.length > 5000 ? execResult.substring(0, 5000) + "\\n...(Truncated)" : execResult;
                    
                    let responseContent = `Command Output:\\n${truncated}`;
                    if (truncated.includes("ERROR:") || truncated.includes("Sandbox Error:")) {
                        responseContent += "\\n\\nCRITICAL SYSTEM WARNING: Your command failed with an error. You MUST analyze this error and use 'file_write', 'replace_file_content', or 'terminal_run' to fix it immediately. Do NOT use the 'done' tool until the script runs successfully without errors!";
                    }
                    
                    history.push({ role: "user", content: responseContent });
                } catch (e: any) {
                    history.push({ role: "user", content: `Sandbox Error:\\n${e.message}\\n\\nCRITICAL SYSTEM WARNING: Your command failed. You MUST fix it immediately. Do NOT use the 'done' tool until the script runs successfully!` });
                }
            } else if (action.tool === "file_write") {
                addMsg("📝 Writing file: " + action.args.path);
                try {
                    const rootUri = vscode.Uri.file("D:\\leif projects");
                    const isAbsolute = action.args.path.startsWith("/") || action.args.path.match(/^[a-zA-Z]:[\\/]/);
                    const targetUri = isAbsolute ? vscode.Uri.file(action.args.path) : vscode.Uri.joinPath(rootUri, action.args.path);
                    
                    // Create parent directory if it doesn't exist
                    try { await vscode.workspace.fs.createDirectory(vscode.Uri.joinPath(targetUri, '..')); } catch (e) {}
                    
                    const createEdit = new vscode.WorkspaceEdit();
                    createEdit.createFile(targetUri, { overwrite: false, ignoreIfExists: true });
                    await vscode.workspace.applyEdit(createEdit);
                    
                    const doc = await vscode.workspace.openTextDocument(targetUri);
                    const fullRange = new vscode.Range(doc.positionAt(0), doc.positionAt(doc.getText().length));
                    const replaceEdit = new vscode.WorkspaceEdit();
                    replaceEdit.replace(targetUri, fullRange, action.args.content);
                    await vscode.workspace.applyEdit(replaceEdit);
                    await doc.save();
                    await vscode.window.showTextDocument(doc);
                    
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `File successfully written to ${targetUri.fsPath}` });
                } catch (err: any) {
                    addMsg("❌ Error writing file: " + err.message);
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `Error writing file: ${err.message}` });
                }
            } else if (action.tool === "file_read") {
                addMsg("📄 Reading file: " + action.args.path);
                try {
                    const rootUri = vscode.Uri.file("D:\\leif projects");
                    const isAbsolute = action.args.path.startsWith("/") || action.args.path.match(/^[a-zA-Z]:[\\/]/);
                    const targetUri = isAbsolute ? vscode.Uri.file(action.args.path) : vscode.Uri.joinPath(rootUri, action.args.path);
                    
                    const data = await vscode.workspace.fs.readFile(targetUri);
                    const content = new TextDecoder("utf-8").decode(data);
                    let finalContent = "";
                    if (action.args.start_line !== undefined && action.args.end_line !== undefined) {
                        const lines = content.split('\\n');
                        const start = Math.max(0, action.args.start_line - 1);
                        const end = Math.min(lines.length, action.args.end_line);
                        finalContent = lines.slice(start, end).join('\\n');
                        if (start > 0) finalContent = `...(Lines 1 to ${start} hidden)...\\n` + finalContent;
                        if (end < lines.length) finalContent += `\\n...(Lines ${end + 1} to ${lines.length} hidden)...`;
                    } else {
                        finalContent = content.length > 5000 ? content.substring(0, 5000) + "\\n...(Truncated)" : content;
                    }
                    
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `File contents:\\n${finalContent}` });
                } catch (err: any) {
                    addMsg("❌ Error reading file: " + err.message);
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `Error reading file: ${err.message}` });
                }
            } else if (action.tool === "list_dir") {
                addMsg("📂 Listing directory: " + action.args.path);
                try {
                    const rootUri = vscode.Uri.file("D:\\leif projects");
                    const isAbsolute = action.args.path.startsWith("/") || action.args.path.match(/^[a-zA-Z]:[\\/]/);
                    const targetUri = isAbsolute ? vscode.Uri.file(action.args.path) : vscode.Uri.joinPath(rootUri, action.args.path);
                    
                    const entries = await vscode.workspace.fs.readDirectory(targetUri);
                    let result = entries.map(e => e[1] === vscode.FileType.Directory ? `[DIR]  ${e[0]}` : `[FILE] ${e[0]}`).join("\\n");
                    if (!result) result = "(Empty Directory)";
                    
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `Directory contents:\\n${result}` });
                } catch (err: any) {
                    addMsg("❌ Error listing directory: " + err.message);
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `Error listing directory: ${err.message}` });
                }
            } else if (action.tool === "replace_file_content") {
                addMsg("✂️ Surgical Edit: " + action.args.path);
                try {
                    const rootUri = vscode.Uri.file("D:\\leif projects");
                    const isAbsolute = action.args.path.startsWith("/") || action.args.path.match(/^[a-zA-Z]:[\\/]/);
                    const targetUri = isAbsolute ? vscode.Uri.file(action.args.path) : vscode.Uri.joinPath(rootUri, action.args.path);
                    
                    const data = await vscode.workspace.fs.readFile(targetUri);
                    let content = new TextDecoder("utf-8").decode(data);
                    
                    if (content.includes(action.args.target_content)) {
                        const doc = await vscode.workspace.openTextDocument(targetUri);
                        const fullRange = new vscode.Range(doc.positionAt(0), doc.positionAt(doc.getText().length));
                        content = content.replace(action.args.target_content, action.args.replacement_content);
                        const replaceEdit = new vscode.WorkspaceEdit();
                        replaceEdit.replace(targetUri, fullRange, content);
                        await vscode.workspace.applyEdit(replaceEdit);
                        await doc.save();
                        await vscode.window.showTextDocument(doc);
                        history.push({ role: "model", content: JSON.stringify(action) });
                        history.push({ role: "user", content: "Surgical replacement successful." });
                    } else {
                        history.push({ role: "model", content: JSON.stringify(action) });
                        history.push({ role: "user", content: "Error: target_content not found in the file exactly as provided." });
                    }
                } catch (err: any) {
                    addMsg("❌ Error replacing content: " + err.message);
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `Error replacing content: ${err.message}` });
                }
            } else if (action.tool === "ask_user") {
                addMsg("🙋 Asking User: " + action.args.question);
                const answer = await vscode.window.showInputBox({ prompt: "Leif asks: " + action.args.question, placeHolder: "Type your answer here..." });
                history.push({ role: "model", content: JSON.stringify(action) });
                if (answer) {
                    history.push({ role: "user", content: `User Answer: ${answer}` });
                    addMsg("👤 User Answered: " + answer);
                    if (answer.trim().toLowerCase() === "stop" || answer.trim().toLowerCase() === "cancel" || answer.trim().toLowerCase() === "exit") {
                        addMsg("🛑 User manually aborted the task.");
                        break;
                    }
                } else {
                    history.push({ role: "user", content: "User skipped or provided no answer." });
                    addMsg("👤 User skipped the question.");
                }
            } else if (action.tool === "search_web") {
                addMsg("🔍 Searching web: " + action.args.query);
                try {
                    const res = await fetch("http://127.0.0.1:8000/api/tools/search", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ query: action.args.query })
                    });
                    const data: any = await res.json();
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `Search Results:\\n${data.result}` });
                } catch (e: any) {
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `Search Error: ${e.message}` });
                }
            } else if (action.tool === "read_url") {
                addMsg("🌐 Reading URL: " + action.args.url);
                try {
                    const res = await fetch("http://127.0.0.1:8000/api/tools/read_url", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ url: action.args.url })
                    });
                    const data: any = await res.json();
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `URL Content:\\n${data.content}` });
                } catch (e: any) {
                    history.push({ role: "model", content: JSON.stringify(action) });
                    history.push({ role: "user", content: `URL Error: ${e.message}` });
                }
            } else {
                history.push({ role: "model", content: JSON.stringify(action) });
                history.push({ role: "user", content: "Unknown tool." });
            }
        }
    }

    private _getHtmlForWebview() {
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Leif Agent Mode</title>
                <style>
                    :root {
                        --leif-accent: #00ffaa;
                        --leif-bg: var(--vscode-editor-background);
                        --leif-fg: var(--vscode-editor-foreground);
                        --leif-input: var(--vscode-input-background);
                        --leif-border: var(--vscode-widget-border);
                    }
                    body {
                        font-family: var(--vscode-font-family);
                        color: var(--leif-fg);
                        background-color: var(--leif-bg);
                        padding: 0;
                        margin: 0;
                        display: flex;
                        flex-direction: column;
                        height: 100vh;
                        box-sizing: border-box;
                        overflow: hidden;
                    }
                    .header {
                        padding: 15px;
                        border-bottom: 1px solid var(--leif-border);
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        background: linear-gradient(180deg, rgba(0,255,170,0.05) 0%, transparent 100%);
                    }
                    h2 {
                        color: var(--leif-accent);
                        font-weight: 600;
                        font-size: 14px;
                        margin: 0;
                        letter-spacing: 0.5px;
                        text-transform: uppercase;
                    }
                    .status-dot {
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background-color: var(--leif-accent);
                        box-shadow: 0 0 8px var(--leif-accent);
                    }
                    .chat-box {
                        flex: 1;
                        overflow-y: auto;
                        padding: 15px;
                        display: flex;
                        flex-direction: column;
                        gap: 15px;
                    }
                    .message {
                        padding: 12px 15px;
                        border-radius: 8px;
                        font-size: 13px;
                        line-height: 1.5;
                        max-width: 90%;
                        word-wrap: break-word;
                    }
                    .msg-user {
                        align-self: flex-end;
                        background-color: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border-bottom-right-radius: 2px;
                    }
                    .msg-leif {
                        align-self: flex-start;
                        background-color: var(--leif-input);
                        border: 1px solid var(--leif-border);
                        border-bottom-left-radius: 2px;
                    }
                    .input-area {
                        padding: 15px;
                        border-top: 1px solid var(--leif-border);
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                        background-color: var(--leif-bg);
                    }
                    textarea {
                        width: 100%;
                        background: var(--leif-input);
                        color: var(--leif-fg);
                        border: 1px solid var(--leif-border);
                        padding: 12px;
                        border-radius: 6px;
                        font-family: inherit;
                        font-size: 13px;
                        resize: none;
                        outline: none;
                        box-sizing: border-box;
                        transition: border-color 0.2s;
                    }
                    textarea:focus {
                        border-color: var(--leif-accent);
                    }
                    button {
                        background: var(--leif-accent);
                        color: #000;
                        border: none;
                        padding: 10px 15px;
                        cursor: pointer;
                        border-radius: 4px;
                        font-weight: 600;
                        font-size: 12px;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        transition: opacity 0.2s;
                        align-self: flex-end;
                    }
                    button:hover {
                        opacity: 0.8;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="status-dot"></div>
                    <h2>Leif Agent</h2>
                </div>
                <div class="chat-box" id="chat">
                    <div class="message msg-leif">
                        Hello! I am connected to your workspace. Give me a task, and I'll execute it right here in your terminal.
                    </div>
                </div>
                <div class="input-area">
                    <textarea id="taskInput" rows="3" placeholder="Ask Leif to scaffold a project, fix a bug, or read a file..."></textarea>
                    <button id="sendBtn">Send Request</button>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();
                    
                    function addMessage(text, isUser) {
                        const chat = document.getElementById('chat');
                        const msg = document.createElement('div');
                        msg.className = 'message ' + (isUser ? 'msg-user' : 'msg-leif');
                        msg.textContent = text;
                        chat.appendChild(msg);
                        chat.scrollTop = chat.scrollHeight;
                    }

                    window.addEventListener('message', event => {
                        const message = event.data;
                        if (message.type === 'addMessage') {
                            addMessage(message.text, message.isUser);
                        }
                    });

                    document.getElementById('sendBtn').addEventListener('click', () => {
                        const input = document.getElementById('taskInput');
                        const text = input.value.trim();
                        if (text) {
                            addMessage(text, true);
                            vscode.postMessage({ type: 'runTask', value: text });
                            input.value = '';
                        }
                    });

                    document.getElementById('taskInput').addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            document.getElementById('sendBtn').click();
                        }
                    });
                </script>
            </body>
            </html>`;
    }
}
