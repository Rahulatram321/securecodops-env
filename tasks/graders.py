from abc import ABC, abstractmethod
from typing import Optional
from env.models import Episode, ActionType, Phase

class BaseGrader(ABC):
    @abstractmethod
    def score_episode(self, episode: Episode) -> float:
        pass

class EasyGrader(BaseGrader):
    def score_episode(self, episode: Episode) -> float:
        if not episode.steps:
            return 0.0
        
        # Find last IDENTIFY_ISSUE action
        identify_actions = [s for s in episode.steps if s.action.action_type == ActionType.IDENTIFY_ISSUE]
        if not identify_actions:
            return 0.0
        
        last_action = identify_actions[-1]
        # Return the reward calculated by Environment for this action
        return last_action.reward

class MediumGrader(BaseGrader):
    def score_episode(self, episode: Episode) -> float:
        if not episode.steps:
            return 0.0
        
        identify_actions = [s for s in episode.steps if s.action.action_type == ActionType.IDENTIFY_ISSUE]
        if not identify_actions:
            return 0.0
        
        last_action = identify_actions[-1]
        return last_action.reward

class HardGrader(BaseGrader):
    def score_episode(self, episode: Episode) -> float:
        if not episode.steps:
            return 0.0
        
        # Trajectory evaluation
        has_reached_final = any(s.observation.current_phase == Phase.FINAL for s in episode.steps)
        last_step = episode.steps[-1]
        
        score = last_step.reward
        
        # Penalty if they didn't reach FINAL phase
        if not has_reached_final:
            score *= 0.5
            
        return float(score)

def get_grader(task_id: str) -> BaseGrader:
    if task_id == "spot_the_bug":
        return EasyGrader()
    elif task_id == "security_audit":
        return MediumGrader()
    elif task_id == "system_debug":
        return HardGrader()
    raise ValueError(f"Unknown task_id: {task_id}")
