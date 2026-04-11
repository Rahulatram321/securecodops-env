"""
SecureCodeOps Inference Script - OpenEnv Hackathon Resubmission
"""
import os
import json
from typing import Dict, List
from openai import OpenAI
from env.environment import SecureCodeOpsEnvironment
from env.models import Action
from baseline.run_baseline import TASK_ACTIONS

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN     = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required.")

BENCHMARK               = os.getenv("BENCHMARK", "securecodops-env")
SUCCESS_SCORE_THRESHOLD = float(os.getenv("SUCCESS_SCORE_THRESHOLD", "0.10"))

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

def llm_ping() -> None:
    try:
        client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Say OK in one word."}],
            max_tokens=8,
            temperature=0,
        )
    except Exception as e:
        print(f"[WARN] LLM ping failed: {e}", flush=True)

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error) -> None:
    done_str  = "true" if done else "false"
    error_str = str(error).replace("\n", "; ") if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_str}", flush=True)

def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_str = "true" if success else "false"
    print(f"[END] success={success_str} steps={steps} rewards={rewards_str}", flush=True)

def run_task(task_id: str, env: SecureCodeOpsEnvironment, planned_actions: List[Dict]) -> None:
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
    rewards: List[float] = []
    steps_taken = 0
    success = False
    try:
        llm_ping()
        env.reset(task_id=task_id)
        for idx, action_payload in enumerate(planned_actions, start=1):
            action = Action(**action_payload)
            result = env.step(action)
            steps_taken = idx
            reward = round(float(result.reward), 2)
            rewards.append(reward)
            done   = bool(result.done)
            error  = getattr(result, "last_action_error", None)
            log_step(step=idx, action=json.dumps(action_payload), reward=reward, done=done, error=error)
            if done:
                break
        score   = rewards[-1] if rewards else 0.0
        success = score >= SUCCESS_SCORE_THRESHOLD
    except Exception as exc:
        steps_taken = max(1, steps_taken)
        if not rewards:
            rewards = [0.0]
        log_step(step=steps_taken, action="error", reward=0.0, done=True, error=str(exc))
        success = False
    finally:
        log_end(success=success, steps=steps_taken, rewards=rewards)

def run() -> None:
    env = SecureCodeOpsEnvironment()
    for task_id, actions in TASK_ACTIONS.items():
        run_task(task_id, env, actions)

if __name__ == "__main__":
    run()
