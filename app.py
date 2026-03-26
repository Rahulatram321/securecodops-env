from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import os
import subprocess
import json

from env.models import Action, StepResult, Observation, Episode
from env.environment import SecureCodeOpsEnvironment
from tasks.task_easy import EasyTask
from tasks.task_medium import MediumTask
from tasks.task_hard import HardTask
from tasks.graders import get_grader

# Global environment instance
env_instance = SecureCodeOpsEnvironment()

# Task instances
tasks = {
    "spot_the_bug": EasyTask(),
    "security_audit": MediumTask(),
    "system_debug": HardTask()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting SecureCodeOpsEnv server...")
    yield
    # Shutdown logic
    print("Shutting down SecureCodeOpsEnv server...")

app = FastAPI(title="SecureCodeOpsEnv", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "env": "securecodops-env"}

@app.post("/reset", response_model=Observation)
async def reset(task_id: str = "spot_the_bug"):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task = tasks[task_id]
    sample = task.get_sample()
    
    return env_instance.reset(task_id=task_id, sample=sample)

@app.post("/step", response_model=StepResult)
async def step(action: Action):
    try:
        if env_instance.state is None:
            raise HTTPException(status_code=400, detail="Environment must be reset before /step")
            
        # Hard task phase progression logic
        if env_instance.state.task_id == "system_debug":
            hard_task = tasks["system_debug"]
            new_phase = hard_task.get_next_phase(env_instance.state.current_phase, action)
            env_instance.state.current_phase = new_phase
            
        return env_instance.step(action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state")
async def get_state():
    return env_instance.get_state()

@app.get("/tasks")
async def get_tasks():
    return [
        {
            "id": t.task_id,
            "difficulty": t.difficulty,
            "description": t.description,
            "max_steps": t.max_steps,
            "action_schema": t.get_action_schema()
        } for t in tasks.values()
    ]

@app.post("/grader")
async def post_grader(payload: Dict[str, str]):
    task_id = payload.get("task_id")
    episode_id = payload.get("episode_id")
    
    if not task_id or not episode_id:
        raise HTTPException(status_code=400, detail="Missing task_id or episode_id")
        
    episode = env_instance.get_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")
        
    grader = get_grader(task_id)
    score = grader.score_episode(episode)
    
    return {"score": float(score)}

@app.post("/baseline")
async def post_baseline():
    # Trigger run_baseline.py
    # Note: In a real production env, this might be async. 
    # For now, we'll run it and return the result.
    try:
        script_path = os.path.join(os.path.dirname(__file__), "baseline", "run_baseline.py")
        result = subprocess.run(["python", script_path], capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": "Baseline failed", "details": result.stderr}
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
