from typing import Optional, Dict, Any
from .models import Action, StepResult, Episode, EpisodeStep, Observation, RewardInfo
from .state import EnvironmentState
from .reward import RewardCalculator
import random # used only for dataset sampling if not provided

class SecureCodeOpsEnvironment:
    def __init__(self):
        self.reward_calculator = RewardCalculator()
        self.state: Optional[EnvironmentState] = None
        self.episodes: Dict[str, Episode] = {}

    def reset(self, task_id: str = "spot_the_bug", sample: Optional[Dict[str, Any]] = None) -> Observation:
        if sample is None:
            # This should be handled by tasks/ logic, but we'll leave a hook here
            raise ValueError("Sample must be provided to reset (handled by tasks/task_*.py)")
            
        self.state = EnvironmentState(task_id, sample)
        
        initial_obs = self.state.get_observation()
        
        episode = Episode(
            episode_id=self.state.episode_id,
            task_id=task_id
        )
        self.episodes[self.state.episode_id] = episode
        
        return initial_obs

    def step(self, action: Action) -> StepResult:
        if self.state is None:
            raise ValueError("Environment must be reset before calling step()")
            
        self.state.step_count += 1
        self.state.action_history.append(action)
        
        reward_info = self.reward_calculator.calculate(
            action=action,
            ground_truth=self.state.ground_truth,
            task_id=self.state.task_id,
            history=self.state.action_history
        )
        
        obs = self.state.get_observation()
        
        # Update episode
        episode = self.episodes[self.state.episode_id]
        episode_step = EpisodeStep(
            step_number=self.state.step_count,
            action=action,
            reward=reward_info.total_reward,
            observation=obs
        )
        episode.steps.append(episode_step)
        episode.total_reward = reward_info.total_reward # Usually we track max reward or last
        
        max_steps = 10
        if self.state.task_id == "spot_the_bug": max_steps = 5
        elif self.state.task_id == "security_audit": max_steps = 7
        
        done = self.state.step_count >= max_steps or reward_info.total_reward >= 0.95
        
        if done:
            episode.is_complete = True
            episode.final_score = reward_info.total_reward

        return StepResult(
            observation=obs,
            reward=reward_info.total_reward,
            done=done,
            info=reward_info
        )

    def get_state(self) -> Dict[str, Any]:
        if self.state is None:
            return {"status": "not_initialized"}
        return self.state.to_dict()

    def get_episode(self, episode_id: str) -> Optional[Episode]:
        return self.episodes.get(episode_id)
