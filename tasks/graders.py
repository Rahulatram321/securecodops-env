import difflib
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
        
        # Find last IDENTIFY_ISSUE
        last_action_step = None
        for s in reversed(episode.steps):
            if s.action.action_type == ActionType.IDENTIFY_ISSUE:
                last_action_step = s
                break
        
        if not last_action_step:
            return 0.0
            
        action = last_action_step.action
        ground_truth = episode.ground_truth or {}
        
        # Line Score
        predicted = set(action.line_numbers or [])
        expected = set(ground_truth.get("lines", []))
        if not expected:
            line_score = 1.0
        else:
            line_score = len(predicted.intersection(expected)) / len(expected)
            
        # Type Score
        gt_type = str(ground_truth.get("type", "")).lower()
        pred_type = str(action.issue_type or "").lower()
        type_score = 1.0 if pred_type == gt_type else 0.0
        
        final = (0.6 * line_score + 0.4 * type_score)
        return float(max(0.0, min(1.0, final)))

class MediumGrader(BaseGrader):
    def score_episode(self, episode: Episode) -> float:
        if not episode.steps:
            return 0.0
            
        last_action_step = None
        for s in reversed(episode.steps):
            if s.action.action_type == ActionType.IDENTIFY_ISSUE:
                last_action_step = s
                break
        
        if not last_action_step:
            return 0.0
            
        action = last_action_step.action
        ground_truth = episode.ground_truth or {}
        
        # CWE/Security Score
        cwe_score = 1.0 if str(action.issue_type or "").lower() == "security" else 0.0
        
        # Line Score
        predicted = set(action.line_numbers or [])
        expected = set(ground_truth.get("lines", []))
        line_score = len(predicted.intersection(expected)) / len(expected) if expected else 1.0
        
        # Fix Score
        predicted_fix = action.suggested_fix or ""
        expected_fix = ground_truth.get("fix", "")
        if not predicted_fix:
            fix_score = 0.0
        else:
            sm = difflib.SequenceMatcher(None, predicted_fix, expected_fix)
            fix_score = float(sm.ratio())
            
        final = (0.3 * cwe_score + 0.3 * line_score + 0.4 * fix_score)
        return float(max(0.0, min(1.0, final)))

class HardGrader(BaseGrader):
    def score_episode(self, episode: Episode) -> float:
        if not episode.steps:
            return 0.0
            
        reached_final = any(s.observation.current_phase == Phase.FINAL for s in episode.steps)
        last_step = episode.steps[-1]
        ground_truth = episode.ground_truth or {}
        
        # 1. Phase Completion (0.3)
        phase_score = 0.3 if reached_final else 0.0
        
        # 2. Correct File Access (0.2)
        requested_files = [s.action.file_name for s in episode.steps if s.action.action_type == ActionType.REQUEST_FILE]
        root_cause = ground_truth.get("root_cause_file", "")
        file_score = 0.2 if root_cause in requested_files else 0.0
        
        # 3. Fix Score (0.3)
        last_action = last_step.action
        if last_action.action_type == ActionType.PROPOSE_FIX and last_action.suggested_fix:
            sm = difflib.SequenceMatcher(None, last_action.suggested_fix, ground_truth.get("fix", ""))
            fix_score = float(sm.ratio()) * 0.3
        else:
            fix_score = 0.0
            
        # 4. Efficiency (0.2)
        if len(episode.steps) <= 5:
            efficiency_score = 0.2
        else:
            efficiency_score = max(0.0, 0.2 * (1 - (len(episode.steps)-5)/10))
            
        if not reached_final:
            episode.missed_issues.append("Agent failed to reach the FINAL reasoning phase.")
            
        return float(max(0.0, min(1.0, phase_score + file_score + fix_score + efficiency_score)))

def get_grader(task_id: str) -> BaseGrader:
    if task_id == "spot_the_bug":
        return EasyGrader()
    elif task_id == "security_audit":
        return MediumGrader()
    elif task_id == "system_debug":
        return HardGrader()
    raise ValueError(f"Unknown task_id: {task_id}")
