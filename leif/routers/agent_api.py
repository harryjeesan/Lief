import os
import json
import tempfile
import subprocess
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from leif.models import AgentRequest, AgentApproveRequest, ExecuteRequest, BrowseRequest, DistillRequest
from leif.agent import agent_loop, project_manager_loop, pending_approvals
from leif.database import save_message, create_conversation

router = APIRouter()

@router.post("/api/agent")
async def start_agent_loop(request: AgentRequest):
    task = request.task.strip()
    execution_mode = "cloud"
    
    is_complex_upwork_job = False
    lower_task = task.lower()
    
    if lower_task.startswith("/project"):
        task = task[8:].strip()
        is_complex_upwork_job = True
    elif not lower_task.startswith("/local") and (
        "we are looking for" in lower_task or 
        "experienced developer" in lower_task or
        "build a modern" in lower_task or
        len(task) > 150 
    ):
        is_complex_upwork_job = True

    if is_complex_upwork_job:
        return StreamingResponse(
            project_manager_loop(task),
            media_type="text/event-stream"
        )
    
    if task.lower().startswith("/local"):
        execution_mode = "local"
        task = task[6:].strip() 
        
    return StreamingResponse(
        agent_loop(task, execution_mode=execution_mode),
        media_type="text/event-stream"
    )

@router.post("/api/agent/approve")
async def approve_agent_action(request: AgentApproveRequest):
    if request.approval_id in pending_approvals:
        pending_approvals[request.approval_id]["approved"] = request.approved
        pending_approvals[request.approval_id]["event"].set()
        return {"status": "success", "approved": request.approved}
    raise HTTPException(status_code=404, detail="Approval ID not found or already processed.")

@router.post("/api/execute")
async def execute_command(request: ExecuteRequest):
    try:
        result = subprocess.run(
            request.command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=15 
        )
        
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        if not output:
            output = "Command executed successfully (no output)."
            
        return {"output": output}
    except Exception as e:
        return {"output": f"Error executing command: {str(e)}"}

@router.post("/api/browse")
async def execute_browse(request: BrowseRequest):
    project_root = os.getcwd()

    boilerplate = f"""
import sys
sys.path.append(r"{project_root}")
from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        try:
{chr(10).join(['            ' + line for line in request.script.split(chr(10))])}
            time.sleep(30)
        except Exception as e:
            print(f"Browser error: {{e}}")
        finally:
            browser.close()

if __name__ == '__main__':
    run()
"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(boilerplate)
            temp_name = f.name
            
        result = subprocess.run(
            f".\\\\venv\\\\Scripts\\\\python.exe {temp_name}", 
            shell=True, capture_output=True, text=True, timeout=45
        )
        os.remove(temp_name)
        
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        if not output:
            output = "Browser macro executed successfully. Video is playing."
        return {"output": output}
    except subprocess.TimeoutExpired:
        os.remove(temp_name)
        return {"output": "Browser script executed and is remaining open for viewing."}
    except Exception as e:
        return {"output": f"Error executing browser script: {str(e)}"}

@router.post("/api/distill")
async def distill_trajectory(request: DistillRequest):
    # Strategy 1: Save to JSONL for future Qwen fine-tuning
    training_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "training_data.jsonl")
    os.makedirs(os.path.dirname(training_file), exist_ok=True)
    
    with open(training_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"task": request.task, "history": request.history}) + "\n")
        
    # Strategy 2: Save to SQLite database so Leif remembers the project in chat
    conv_id = create_conversation()
    save_message("user", request.task, conversation_id=conv_id)
    
    # Extract the final answer from the history if available
    final_answer = "Completed Agent Task."
    if request.history and len(request.history) > 0:
        last_action = request.history[-1].get("content", "")
        try:
            action_data = json.loads(last_action)
            if action_data.get("tool") == "done":
                final_answer = action_data.get("args", {}).get("message", final_answer)
        except Exception:
            pass
            
    save_message("leif", f"I successfully completed your VS Code Agent Task!\\nFinal Output: {final_answer}", conversation_id=conv_id)
    
    return {"status": "success"}
