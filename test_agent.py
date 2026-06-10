import requests
import json
import psutil
import threading
import time

TASK = "I need a python script called monitor.py that checks how much free space is left on my C drive in GB. Write it, run it to test it, and then save the project to long-term memory."

print("=== LEIF AGENT TESTER ===")
print(f"Task: {TASK}")
print("=========================")

# Monitor system conditions
def monitor_system():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        print(f"[SYSTEM] CPU: {cpu}% | RAM: {mem}%")
        time.sleep(2)

t = threading.Thread(target=monitor_system, daemon=True)
t.start()

start_time = time.time()
try:
    response = requests.post(
        "http://127.0.0.1:8000/api/agent",
        json={"task": TASK},
        stream=True,
        timeout=120
    )
    
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                event_str = decoded[6:]
                try:
                    event = json.loads(event_str)
                    typ = event.get('type')
                    if typ == 'status':
                        print(f"STATUS: {event.get('message')}")
                    elif typ == 'thought':
                        print(f"THOUGHT: {event.get('message')}")
                    elif typ == 'action_result':
                        print(f"RESULT ({event.get('tool')}): {event.get('result')[:100]}...")
                    elif typ == 'requires_approval':
                        tool = event.get('tool')
                        args = event.get('args')
                        app_id = event.get('approval_id')
                        print(f"REQUIRES APPROVAL: {tool} with args {args}")
                        # Auto-approve
                        requests.post("http://127.0.0.1:8000/api/agent/approve", json={
                            "approval_id": app_id,
                            "approved": True
                        })
                        print(f"Auto-approved {app_id}")
                    elif typ == 'done':
                        print(f"TASK COMPLETE: {event.get('message')}")
                        break
                    elif typ == 'error':
                        print(f"ERROR: {event.get('message')}")
                        break
                except Exception as e:
                    print(f"Parse error: {e}")
                    
except Exception as e:
    print(f"Request failed: {e}")

duration = time.time() - start_time
print(f"\n=========================")
print(f"Test completed in {duration:.1f} seconds")
print("=========================")
