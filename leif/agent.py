import json
import asyncio
import uuid
import subprocess
import os
from dotenv import load_dotenv
from leif.database import save_long_term_memory, search_memories
from google.genai import types
from leif.llm_router import generate_with_fallback
from leif.local_llm import generate_local_json
from datetime import datetime
import json
import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# In-memory registry for blocking the agent until the UI approves
pending_approvals = {}

def save_trajectory(task: str, history: list, execution_mode: str):
    """
    Saves a successful agent loop trajectory to disk in ShareGPT format
    for fine-tuning the local phi3:mini model.
    """
    DATA_DIR = r"D:\\Leif_Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    # Both Cloud and Local successful runs will be merged into a single training dataset.
    # Cloud runs teach the local model how Groq codes.
    # Local runs that succeed reinforce the local model's good behavior (Self-Play/RLHF style).
    filename = "distilled_trajectories.jsonl"
    filepath = os.path.join(DATA_DIR, filename)
    
    # Format for Unsloth / ShareGPT
    # We want the model to predict the full JSON loop
    messages = [
        {"role": "user", "content": f"Task: {task}\n\nWhat is your next action?"}
    ]
    
    # The history contains the exact JSON outputs (the thought/tool/args)
    # We stringify the entire history as the "assistant" response so the local
    # model learns the exact ReAct loop pattern.
    assistant_content = json.dumps(history, indent=2)
    messages.append({"role": "assistant", "content": assistant_content})
    
    jsonl_obj = {"conversations": messages, "timestamp": datetime.now().isoformat()}
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(jsonl_obj, ensure_ascii=False) + "\\n")

def execute_tool(tool: str, args: dict) -> str:
    if tool == "consult_cloud":
        try:
            question = args.get("question", "")
            res = generate_with_fallback(
                contents=[{"role": "user", "parts": [{"text": f"You are a Senior Cloud Consultant. The local offline LLM needs your exact code or advice to proceed. Provide a direct, concise answer.\n\nQuestion: {question}"}]}],
                config=types.GenerateContentConfig(temperature=0.2)
            )
            return res.text
        except Exception as e:
            return f"Error consulting cloud: {e}"
            
    elif tool == "search_web":
        try:
            query = args.get("query", "")
            results = DDGS().text(query, max_results=5)
            if not results:
                return "No search results found."
            formatted = "\\n".join([f"[{i+1}] {r['title']}\\nURL: {r['href']}\\nSnippet: {r['body']}\\n" for i, r in enumerate(results)])
            return f"Search Results:\\n{formatted}"
        except Exception as e:
            return f"Error searching the web: {e}"
            
    elif tool == "read_url":
        try:
            url = args.get("url", "")
            with httpx.Client(follow_redirects=True, timeout=15) as client:
                res = client.get(url)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, "html.parser")
                text = soup.get_text(separator='\\n', strip=True)
                return text[:15000] + "\\n...(Truncated)" if len(text) > 15000 else text
        except Exception as e:
            return f"Error reading URL: {e}"
            
    elif tool == "terminal_run":
        try:
            res = subprocess.run(args.get("command", ""), shell=True, capture_output=True, text=True, timeout=15)
            output = res.stdout.strip() if res.stdout else res.stderr.strip()
            if not output:
                return "Command executed successfully (no output)."
            return output[:5000] + "\n...(Truncated)" if len(output) > 5000 else output
        except Exception as e:
            return f"Error: {e}"
            
    elif tool == "file_write":
        try:
            path = args.get("path", "")
            if os.path.dirname(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(args.get("content", ""))
            return f"Successfully saved {path}"
        except Exception as e:
            return f"Error: {e}"
            
    elif tool == "file_read":
        try:
            with open(args.get("path", ""), "r", encoding="utf-8") as f:
                content = f.read()
            return content[:5000] + "\n...(Truncated)" if len(content) > 5000 else content
        except Exception as e:
            return f"Error: {e}"
            
    elif tool == "save_memory":
        try:
            topic = args.get("topic", "General")
            summary = args.get("summary", "")
            code_snippets = args.get("code_snippets", "")
            success = save_long_term_memory(topic, summary, code_snippets)
            return "Successfully saved memory to ChromaDB" if success else "Failed to save memory."
        except Exception as e:
            return f"Error: {e}"
            
    return "Tool not found"

async def wait_for_approval(approval_id: str) -> bool:
    """Blocks the loop until the frontend hits the /api/agent/approve endpoint or times out."""
    event = asyncio.Event()
    pending_approvals[approval_id] = {"event": event, "approved": False}
    try:
        # 10 minute timeout to prevent background memory leaks
        await asyncio.wait_for(event.wait(), timeout=600)
        return pending_approvals.pop(approval_id)["approved"]
    except asyncio.TimeoutError:
        pending_approvals.pop(approval_id, None)
        return False

async def project_manager_loop(task: str):
    """
    Acts as an orchestrator, breaking a massive prompt into milestones,
    and then chaining agent_loop calls for each milestone.
    """
    yield f"data: {json.dumps({'type': 'status', 'message': '👔 Project Manager: Analyzing your request...'})}\n\n"
    
    system_prompt = """You are a Senior Technical Architect. The user wants to build a complex project.
If the user's request is vague (e.g., 'build a biotech website'), you MUST automatically flesh out the design language, tech stack, and necessary features to make it a premium, production-grade product. 
CRITICAL RULE: NEVER use Vanilla JS/HTML for modern websites. You MUST explicitly plan the project using modern frameworks (e.g., React, Next.js, Vite with react-ts) and modern styling (e.g., Tailwind CSS, Framer Motion).
Break the project down into a strict sequential list of 3 to 7 milestones.
Each milestone MUST be an extremely detailed string describing EXACTLY what needs to be built in that step.
Return ONLY valid JSON in this exact format:
{
    "milestones": [
        "Milestone 1: ...",
        "Milestone 2: ..."
    ]
}"""

    try:
        response = generate_with_fallback(
            contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\nTask: " + task}]}],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
            is_json_mode=True
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").strip("json").strip()
            
        plan = json.loads(raw_text)
        milestones = plan.get("milestones", [task])
        
        yield f"data: {json.dumps({'type': 'status', 'message': f'📋 Project Manager created {len(milestones)} milestones!'})}\n\n"
        
        # We will accumulate context so the agent knows what it just did
        context_chain = ""
        
        for i, milestone in enumerate(milestones):
            yield f"data: {json.dumps({'type': 'status', 'message': f'🚀 STARTING MILESTONE {i+1}/{len(milestones)}'})}\n\n"
            
            # Construct the prompt for the agent
            agent_task = f"MASTER PROJECT GOAL: {task}\n\n"
            if context_chain:
                agent_task += f"COMPLETED MILESTONES:\\n{context_chain}\n\n"
            agent_task += f"YOUR CURRENT MILESTONE ({i+1}/{len(milestones)}):\\n{milestone}\n\nFocus ONLY on completing this current milestone."
            
            # Run the agent loop for this milestone
            async for chunk in agent_loop(agent_task, max_iterations=50, execution_mode="cloud"):
                yield chunk
                
            # Update context for the next milestone
            context_chain += f"- {milestone}\\n"
            
        yield f"data: {json.dumps({'type': 'status', 'message': '🎉 ALL MILESTONES COMPLETED!'})}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'Project Manager Error: {str(e)}'})}\n\n"

async def agent_loop(task: str, max_iterations: int = 50, execution_mode: str = "cloud"):
    """
    The core ReAct loop. Yields Server-Sent Events (SSE).
    """
    history = []
    
    yield f"data: {json.dumps({'type': 'status', 'message': f'🚀 Initializing Agent Loop ({execution_mode.upper()} MODE)...'})}\n\n"
    
    for i in range(max_iterations):
        yield f"data: {json.dumps({'type': 'status', 'message': '🧠 Thinking...'})}\n\n"
        
        core_memories = search_memories(task)
        
        # In Local Mode, we give Leif the ability to consult the cloud
        consult_cloud_tool = '8. "consult_cloud" - args: {"question": "what you need help with"} (Use this if you do not know the exact code or steps. The Cloud will give you the answer, then use file_write to apply it.)' if execution_mode == "local" else ""
        
        system_prompt = f"""You are an autonomous ReAct agent. You MUST respond in pure JSON.
Available tools:
1. "terminal_run" - args: {{"command": "shell command"}} (Use ONLY for shell commands like npm, dir, cd, etc. DO NOT use this to run the file_write tool)
2. "file_write" - args: {{"path": "file path", "content": "file content"}} (Use this tool to create or overwrite files. It is NOT a terminal command)
3. "file_read" - args: {{"path": "file path"}} (Use this tool to read the contents of an existing file so you can analyze it)
4. "save_memory" - args: {{"topic": "short topic", "summary": "detailed summary of learnings", "code_snippets": "optional code"}}
5. "search_web" - args: {{"query": "search term"}} (Use this tool to search the internet for documentation, errors, or APIs)
6. "read_url" - args: {{"url": "https://..."}} (Use this tool to extract readable text from a URL found in search results)
7. "done" - args: {{"message": "final answer to user"}}
{consult_cloud_tool}

STANDARD OPERATING PROCEDURES (SOP) FOR UPWORK-LEVEL TASKS:
Phase 1: Discovery & Scaffolding
- NEVER assume file structures. If modifying a project, use `terminal_run` (e.g., `dir /B /S`) or `file_read` (on package.json/requirements.txt) to understand the workspace.
- If you encounter an API you don't know, immediately use `search_web`. DO NOT guess syntax.
Phase 2: Execution
- Write files sequentially. If creating an app, run the scaffold command first, then verify the folder exists before writing components.
Phase 3: Verification
- Do not call the `done` tool until the task is completely finished AND verified. If you write code, run it.
- Use `terminal_run` to run builds (`npm run build`, `python -m pytest`, etc.) and read the output. If it fails, debug it.

CRITICAL RULES FOR WEB DEVELOPMENT:
1. Stateful Terminals: Every time you run a terminal command, the working directory resets to the root folder. If you create a new app folder (e.g., `my-app`), you MUST prefix all future commands with `cd my-app &&` (e.g., `cd my-app && npm install`).
2. Non-Interactive Commands: Terminal commands run in the background without user interaction. If a command prompts for input (like `npx create-vite`), it will crash or output default vanilla templates. You MUST pass flags to avoid prompts (e.g., `npx create-vite@latest my-app --template react-ts`).
3. Relentless Execution: Do not call the `done` tool until the ENTIRE task is completely finished. Scaffold, install, write code, and verify before stopping.
4. Storage: You MUST build all client projects inside the `D:\\Upwork_Projects` directory. Create this directory if it does not exist. Use absolute paths for all file_write tools and cd into this drive/directory for all terminal commands (e.g., `cd /d D:\\Upwork_Projects && npx create-next-app...`).
{ "5. LOCAL MODE: If you do not know how to do something, do NOT guess. Use the consult_cloud tool to ask your senior cloud engineers for the exact code, then use file_write to apply their advice yourself." if execution_mode == "local" else "" }

{core_memories}

Output format:
{{
    "current_subtask": "Briefly describe what micro-goal you are currently pursuing",
    "thought": "your step-by-step reasoning",
    "tool": "tool_name",
    "args": {{ ... }}
}}"""
        
        # Prevent context explosion for Groq (8k limit) by keeping only the last 8 actions
        truncated_history = history[-8:] if len(history) > 8 else history
        user_prompt = f"Task: {task}\n\nExecution History (Last {len(truncated_history)} steps):\n{json.dumps(truncated_history, indent=2)}\n\nWhat is your next action?"
        
        try:
            if execution_mode == "local":
                raw_text = generate_local_json(system_prompt, user_prompt)
            else:
                # Using robust router for high-reliability JSON output
                response = generate_with_fallback(
                    contents=[
                        {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}
                    ],
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                    is_json_mode=True
                )
                
                # Extract token count safely depending on if it's Gemini or Groq
                token_count = 0
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    token_count = response.usage_metadata.total_token_count
                
                if token_count > 0:
                    yield f"data: {json.dumps({'type': 'status', 'message': f'📊 Token Usage: {token_count} tokens...'})}\n\n"
                
                raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`").strip("json").strip()
                
            try:
                action = json.loads(raw_text, strict=False)
            except json.JSONDecodeError as e:
                if "escape" in str(e).lower():
                    try:
                        fixed_text = raw_text.replace('\\', '\\\\').replace('\\\\n', '\\n').replace('\\\\"', '\\"').replace('\\\\t', '\\t').replace('\\\\r', '\\r')
                        action = json.loads(fixed_text, strict=False)
                    except json.JSONDecodeError as e2:
                        history.append({"result": f"SYSTEM ERROR: Invalid JSON format. {e2}. You MUST output ONLY valid JSON without any prefix or suffix."})
                        yield f"data: {json.dumps({'type': 'status', 'message': '⚠️ Recovering from bad JSON formatting...'})}\n\n"
                        continue
                else:
                    history.append({"result": f"SYSTEM ERROR: Invalid JSON format. {e}. You MUST output ONLY valid JSON without any prefix or suffix."})
                    yield f"data: {json.dumps({'type': 'status', 'message': '⚠️ Recovering from bad JSON formatting...'})}\n\n"
                    continue
            current_subtask = action.get("current_subtask", "")
            thought = action.get("thought", "")
            tool = action.get("tool", "done")
            args = action.get("args", {})
            
            if current_subtask:
                yield f"data: {json.dumps({'type': 'status', 'message': f'🎯 Goal: {current_subtask}'})}\n\n"
            yield f"data: {json.dumps({'type': 'thought', 'message': thought})}\n\n"
            
            if tool == "done":
                # AUTO-DISTILLATION: Save the successful trajectory
                try:
                    save_trajectory(task, history, execution_mode)
                    yield f"data: {json.dumps({'type': 'status', 'message': f'💾 Trajectory saved for distillation!'})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to save trajectory: {e}'})}\n\n"
                    
                yield f"data: {json.dumps({'type': 'done', 'message': args.get('message', 'Task Complete')})}\n\n"
                break
                
            # Yield approval request for sensitive tools
            if tool in ["terminal_run", "file_write"]:
                approval_id = str(uuid.uuid4())
                yield f"data: {json.dumps({'type': 'requires_approval', 'approval_id': approval_id, 'tool': tool, 'args': args})}\n\n"
                
                # Block until frontend approves
                approved = await wait_for_approval(approval_id)
                
                if not approved:
                    yield f"data: {json.dumps({'type': 'status', 'message': '❌ Action rejected by user.'})}\n\n"
                    history.append({"thought": thought, "tool": tool, "args": args, "result": "REJECTED BY USER"})
                    continue
                    
                yield f"data: {json.dumps({'type': 'status', 'message': f'🔧 Executing {tool}...'})}\n\n"
                
            # Execute the tool
            result = execute_tool(tool, args)
            history.append({"thought": thought, "tool": tool, "args": args, "result": result})
            
            yield f"data: {json.dumps({'type': 'action_result', 'tool': tool, 'result': result})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            break
