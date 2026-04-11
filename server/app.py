from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import os
import json

from env.models import Action, StepResult, Observation, Episode
from env.environment import SecureCodeOpsEnvironment
from tasks.task_easy import EasyTask
from tasks.task_medium import MediumTask
from tasks.task_hard import HardTask
from tasks.graders import get_grader

# Global environment instance
env_instance = SecureCodeOpsEnvironment()

# Task instances for schema/metadata
tasks = {
    "spot_the_bug": EasyTask(),
    "security_audit": MediumTask(),
    "system_debug": HardTask()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting SecureCodeOpsEnv server... [v1.2.0]")
    yield
    print("Shutting down SecureCodeOpsEnv server...")

app = FastAPI(title="SecureCodeOpsEnv", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "name": "SecureCodeOpsEnv", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok", "env": "securecodops-env", "version": "1.2.0"}

# ── /reset  accepts BOTH query-param and JSON body so the validator never 404s ──
@app.post("/reset")
async def reset(request: Request, task_id: Optional[str] = None):
    """Reset the environment. Accepts task_id as query param OR in JSON body."""
    # Try to read from JSON body first, then fall back to query param
    if task_id is None:
        try:
            body = await request.json()
            task_id = body.get("task_id", "spot_the_bug") if body else "spot_the_bug"
        except Exception:
            task_id = "spot_the_bug"

    try:
        obs = env_instance.reset(task_id=task_id)
        return {
            "observation": obs.model_dump(),
            "done": False,
            "reward": 0.0,
            "episode_id": env_instance.state.episode_id,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── /step  returns the exact fields the validator checks ──
@app.post("/step")
async def step(action: Action):
    if env_instance.state is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    try:
        result = env_instance.step(action)
        return {
            "observation": result.observation.model_dump(),
            "reward": float(result.reward),
            "done": result.done,
            "last_action_error": None,
            "info": result.info.model_dump(),
        }
    except Exception as e:
        return {
            "observation": {},
            "reward": 0.0,
            "done": True,
            "last_action_error": str(e),
        }

@app.get("/state")
async def get_state():
    return env_instance.get_state()

@app.post("/close")
async def close():
    """Close the current episode and reset environment state."""
    try:
        env_instance.close()
        return {"status": "closed"}
    except Exception as e:
        return {"status": "closed", "detail": str(e)}

@app.get("/tasks")
async def get_tasks():
    return {
        "tasks": [
            {
                "id": t.task_id,
                "difficulty": t.difficulty,
                "description": getattr(t, "description", "Identify and fix software defects."),
                "action_schema": t.get_action_schema()
            } for t in tasks.values()
        ]
    }

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
    
    return {
        "episode_id": episode_id,
        "task_id": task_id,
        "score": float(score),
        "missed_issues": episode.missed_issues,
        "false_positives": episode.false_positives,
        "reasoning_gap": episode.reasoning_gap or "No reasoning gap identified"
    }

@app.post("/baseline")
async def post_baseline(request: Request):
    from baseline.run_baseline import run_adaptive_baseline
    try:
        scores = run_adaptive_baseline()
        return {"baseline_scores": scores, "status": "complete"}
    except Exception as e:
        return {"error": "Baseline failed", "detail": str(e)}

@app.get("/episode_summary")
async def get_episode_summary(episode_id: str):
    episode = env_instance.get_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    return {
        "episode_id": episode.episode_id,
        "task_id": episode.task_id,
        "total_steps": len(episode.steps),
        "total_reward": episode.total_reward,
        "final_score": episode.final_score,
        "is_complete": episode.is_complete,
        "missed_issues": episode.missed_issues,
        "false_positives": episode.false_positives,
        "reasoning_gap": episode.reasoning_gap,
        "step_rewards": [round(s.reward, 4) for s in episode.steps]
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)}
    )

def start():
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    start()
