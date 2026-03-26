import uuid
from typing import Dict, Any, List
from .models import Observation, Phase

class EnvironmentState:
    def __init__(self, task_id: str, sample: Dict[str, Any]):
        self.task_id = task_id
        self.sample = sample
        self.ground_truth = sample.get("ground_truth", {})
        self.step_count = 0
        self.episode_id = str(uuid.uuid4())
        self.action_history = []
        self.revealed_files = {}
        self.hints_used = 0
        
        # Hard task specific
        self.current_phase = Phase.INIT if task_id == "system_debug" else None
        self.available_files = sample.get("available_files", [])
        self.file_contents = sample.get("file_contents", {})

    def get_observation(self) -> Observation:
        obs_data = {
            "task_id": self.task_id,
            "step_count": self.step_count,
            "revealed_files": self.revealed_files,
            "hints_used": self.hints_used,
            "current_phase": self.current_phase,
        }

        if self.task_id in ["spot_the_bug", "security_audit"]:
            obs_data.update({
                "code_snippet": self.sample.get("code"),
                "language": self.sample.get("language"),
                "context": self.sample.get("context", "Analyze the code for bugs or vulnerabilities."),
                "max_steps": 5 if self.task_id == "spot_the_bug" else 7
            })
        elif self.task_id == "system_debug":
            obs_data.update({
                "logs": self.sample.get("logs"),
                "stack_trace": self.sample.get("stack_trace"),
                "available_files": self.available_files,
                "max_steps": 10
            })

        return Observation(**obs_data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "task_id": self.task_id,
            "step_count": self.step_count,
            "current_phase": self.current_phase,
            "history_length": len(self.action_history),
            "revealed_files_count": len(self.revealed_files)
        }
