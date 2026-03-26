import requests
import json
import os
import sys

def run_baseline(base_url: str = None) -> dict:
    if base_url is None:
        base_url = os.getenv("BASE_URL", "http://localhost:7860")
    
    results = {}
    task_ids = ["spot_the_bug", "security_audit", "system_debug"]
    
    for task_id in task_ids:
        try:
            # 1. Reset
            reset_resp = requests.post(f"{base_url}/reset?task_id={task_id}")
            if reset_resp.status_code != 200:
                results[task_id] = 0.0
                continue
            
            obs = reset_resp.json()
            
            # 2. Heuristic Action based on task
            action_data = {
                "action_type": "IDENTIFY_ISSUE",
                "confidence": 0.8,
                "explanation": "Heuristic baseline identifies common patterns."
            }
            
            if task_id == "spot_the_bug":
                action_data.update({"line_numbers": [2], "issue_type": "BUG", "severity": "MEDIUM"})
            elif task_id == "security_audit":
                action_data.update({"line_numbers": [3], "issue_type": "SECURITY", "severity": "HIGH", "suggested_fix": "Fix it."})
            elif task_id == "system_debug":
                 # Hard task needs multiple steps ideally, but we'll do one identification
                 action_data.update({"action_type": "FORM_HYPOTHESIS", "hypothesis": "Race condition in db.py"})

            # 3. Step
            step_resp = requests.post(f"{base_url}/step", json=action_data)
            if step_resp.status_code == 200:
                results[task_id] = step_resp.json()["reward"]
            else:
                results[task_id] = 0.0
                
        except Exception as e:
            results[task_id] = 0.0
            
    return results

if __name__ == "__main__":
    # If running normally, we assume server is already up.
    # If triggered via /baseline in app.py, base_url is same.
    scores = run_baseline()
    print(json.dumps(scores, indent=2))
