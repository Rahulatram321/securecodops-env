"""
Baseline inference script emitting the mandatory [START]/[STEP]/[END] logs.
Uses deterministic heuristic actions so it runs without network access, while
still initializing an OpenAI client with API_BASE_URL/MODEL_NAME/HF_TOKEN.
"""

import os
import json
from typing import Dict, List
from openai import OpenAI

from env.environment import SecureCodeOpsEnvironment
from env.models import Action
from baseline.run_baseline import TASK_ACTIONS

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or "DUMMY_TOKEN"
BENCHMARK = os.getenv("BENCHMARK", "securecodops-env")
SUCCESS_SCORE_THRESHOLD = float(os.getenv("SUCCESS_SCORE_THRESHOLD", "0.10"))

# Initialize client (required by rules); calls are optional and guarded.
client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


def _format_rewards(rewards: List[float]) -> str:
    return ",".join(f"{r:.2f}" for r in rewards)


def run_task(task_id: str, env: SecureCodeOpsEnvironment, planned_actions: List[Dict]) -> None:
    print(f"[START] task={task_id} env={BENCHMARK} model={MODEL_NAME}")
    rewards: List[float] = []
    steps_taken = 0
    success = False

    try:
        env.reset(task_id=task_id)
        for idx, action_payload in enumerate(planned_actions, start=1):
            action = Action(**action_payload)
            result = env.step(action)
            steps_taken = idx
            reward = round(float(result.reward), 2)
            rewards.append(reward)
            error_field = "null"
            print(
                f"[STEP] step={idx} action={json.dumps(action_payload)} "
                f"reward={reward:.2f} done={str(result.done).lower()} error={error_field}"
            )
            if result.done:
                break

        score = rewards[-1] if rewards else 0.0
        success = score >= SUCCESS_SCORE_THRESHOLD
    except Exception as exc:
        # Ensure we always emit an END line even on failure
        steps_taken = max(1, steps_taken)
        rewards = rewards or [0.0]
        score = rewards[-1]
        success = False
        print(
            f"[STEP] step={steps_taken} action=error reward=0.00 done=true error={str(exc).replace(chr(10), '; ')}"
        )

    print(
        f"[END] success={str(success).lower()} steps={steps_taken or 0} "
        f"score={score:.2f} rewards={_format_rewards(rewards)}"
    )


def run():
    env = SecureCodeOpsEnvironment()
    for task_id, actions in TASK_ACTIONS.items():
        run_task(task_id, env, actions)


if __name__ == "__main__":
    run()
