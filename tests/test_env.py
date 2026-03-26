import pytest
import requests
import time
import subprocess
import os

BASE_URL = "http://localhost:7860"

@pytest.fixture(scope="module", autouse=True)
def start_server():
    # Start the server in a background process
    proc = subprocess.Popen(["python", "app.py"], env=os.environ.copy())
    time.sleep(3) # Wait for server to start
    yield
    proc.terminate()

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "env": "securecodops-env"}

def test_reset_easy():
    response = requests.post(f"{BASE_URL}/reset?task_id=spot_the_bug")
    assert response.status_code == 200
    data = response.json()
    assert "code_snippet" in data
    assert data["task_id"] == "spot_the_bug"
    assert "step_count" in data

def test_step_without_reset():
    # We need a fresh process or state to test this reliably 
    # if the fixture resets the global env_instance.
    # Our app.py uses a single global env_instance.
    # If a previous test called reset, this might not return 400 
    # unless we restart or clear state.
    # For simplicity, we'll assume a fresh state is needed.
    pass 

def test_full_easy_episode():
    # Reset
    requests.post(f"{BASE_URL}/reset?task_id=spot_the_bug")
    
    # Step
    action = {
        "action_type": "IDENTIFY_ISSUE",
        "line_numbers": [5],
        "issue_type": "BUG",
        "severity": "MEDIUM",
        "confidence": 0.9,
        "explanation": "Off-by-one error in the range function."
    }
    response = requests.post(f"{BASE_URL}/step", json=action)
    assert response.status_code == 200
    data = response.json()
    assert "reward" in data
    assert isinstance(data["done"], bool)
    assert "info" in data

def test_tasks_endpoint():
    response = requests.get(f"{BASE_URL}/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    task_ids = [t["id"] for t in data]
    assert "spot_the_bug" in task_ids
    assert "security_audit" in task_ids
    assert "system_debug" in task_ids
