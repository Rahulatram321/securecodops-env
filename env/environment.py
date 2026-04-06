import os
import json
import random
import uuid
from typing import Optional, Dict, Any, List
from .models import Action, StepResult, Episode, EpisodeStep, Observation, ActionType, Phase
from .reward import RewardCalculator

class EnvironmentState:
    def __init__(self, task_id: str, sample: Dict[str, Any]):
        self.task_id = task_id
        self.sample = sample
        self.ground_truth = sample.get("ground_truth", {})
        self.step_count = 0
        self.episode_id = str(uuid.uuid4())
        self.current_phase = Phase.INIT
        self.action_history = []
        self.revealed_files = {}
        self.file_contents = sample.get("file_contents", {})

    def get_observation(self) -> Observation:
        if self.task_id == "system_debug":
            return Observation(
                task_id=self.task_id,
                step_count=self.step_count,
                revealed_files=self.revealed_files,
                current_phase=self.current_phase,
                logs=self.sample.get("logs"),
                stack_trace=self.sample.get("stack_trace"),
                available_files=list(self.file_contents.keys()),
                metadata={
                    "episode_id": self.episode_id,
                    "difficulty": "hard"
                }
            )
        else:
            return Observation(
                task_id=self.task_id,
                step_count=self.step_count,
                code_snippet=self.sample.get("code"),
                language=self.sample.get("language", "python"),
                context=self.sample.get("context", "Analyze the code for bugs or vulnerabilities."),
                revealed_files=self.revealed_files,
                metadata={
                    "episode_id": self.episode_id
                }
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "task_id": self.task_id,
            "step_count": self.step_count,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "history_length": len(self.action_history)
        }

class SecureCodeOpsEnvironment:
    def __init__(self):
        self.reward_calculator = RewardCalculator()
        self.state: Optional[EnvironmentState] = None
        self.episodes: Dict[str, Episode] = {}

    def _load_sample(self, task_id: str) -> Dict[str, Any]:
        file_map = {
            "spot_the_bug": "easy_samples.json",
            "security_audit": "medium_samples.json",
            "system_debug": "hard_samples.json"
        }
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_path, "tasks", "dataset", file_map[task_id])
        
        with open(file_path, "r") as f:
            samples = json.load(f)
        return random.choice(samples)

    def reset(self, task_id: str = "spot_the_bug") -> Observation:
        if task_id not in ["spot_the_bug", "security_audit", "system_debug"]:
            raise ValueError(f"Invalid task_id: {task_id}")
            
        sample = self._load_sample(task_id)
        self.state = EnvironmentState(task_id, sample)
        
        episode = Episode(
            episode_id=self.state.episode_id,
            task_id=task_id,
            steps=[],
            ground_truth=sample.get("ground_truth", {})
        )
        self.episodes[self.state.episode_id] = episode
        
        return self.state.get_observation()

    def step(self, action: Action) -> StepResult:
        if self.state is None:
            raise ValueError("Environment must be reset before calling step()")
            
        penalty = 0.0
        
        # Hard task phase and reveal logic
        if self.state.task_id == "system_debug":
            from tasks.task_hard import HardTask
            ht = HardTask()
            allowed = ht.ALLOWED_ACTIONS.get(self.state.current_phase, [])
            if action.action_type not in allowed:
                penalty += 0.1
            
            if action.action_type == ActionType.REQUEST_FILE and action.file_name:
                content = self.state.file_contents.get(action.file_name, "File not found")
                if self.state.current_phase in [Phase.ROOT_CAUSE, Phase.FINAL]:
                    revealed = content
                else:
                    revealed = "\n".join(content.splitlines()[:5]) + "\n... [Snippet Restricted] ..."
                self.state.revealed_files[action.file_name] = revealed
            
            self.state.current_phase = ht.get_next_phase(self.state.current_phase, action)

        self.state.step_count += 1
        self.state.action_history.append(action)
        
        reward_info = self.reward_calculator.calculate(
            action, 
            self.state.ground_truth, 
            self.state.task_id, 
            self.state.action_history
        )
        
        final_reward = max(0.0, min(1.0, reward_info.total_reward - penalty))
        reward_info.total_reward = final_reward
        
        obs = self.state.get_observation()
        
        episode_step = EpisodeStep(
            step_number=self.state.step_count,
            action=action,
            reward=final_reward,
            observation=obs
        )
        
        episode = self.episodes[self.state.episode_id]
        episode.steps.append(episode_step)
        episode.total_reward += final_reward
        
        # task-specific max steps
        max_steps = 10
        if self.state.task_id == "spot_the_bug":
            max_steps = 5
        elif self.state.task_id == "security_audit":
            max_steps = 7

        done = self.state.step_count >= max_steps or final_reward >= 0.95
        if done:
            episode.is_complete = True
            episode.final_score = final_reward
            
        return StepResult(
            observation=obs,
            reward=final_reward,
            done=done,
            info=reward_info
        )

    def get_state(self) -> Dict[str, Any]:
        if self.state:
            return self.state.to_dict()
        return {"status": "not_initialized"}

    def get_episode(self, episode_id: str) -> Optional[Episode]:
        return self.episodes.get(episode_id)
