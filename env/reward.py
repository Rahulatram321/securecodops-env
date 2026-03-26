from difflib import SequenceMatcher
from typing import List, Dict, Any
from .models import Action, RewardInfo, IssueType

class RewardCalculator:
    def calculate(self, action: Action, ground_truth: Dict[str, Any], 
                  task_id: str, history: List[Any]) -> RewardInfo:
        
        # 1. Line Detection Score
        expected_lines = set(ground_truth.get("lines", []))
        predicted_lines = set(action.line_numbers or [])
        
        if not expected_lines:
            line_detection_score = 1.0 if not predicted_lines else 0.0
        else:
            intersection = expected_lines.intersection(predicted_lines)
            line_detection_score = len(intersection) / len(expected_lines)

        # 2. Issue Classification Score
        expected_type = ground_truth.get("type", "").upper()
        predicted_type = action.issue_type.value if action.issue_type else ""
        
        if predicted_type == expected_type:
            issue_classification_score = 1.0
        elif (predicted_type in ["BUG", "LOGIC"] and expected_type in ["BUG", "LOGIC"]):
            issue_classification_score = 0.5
        else:
            issue_classification_score = 0.0

        # 3. Fix Quality Score
        predicted_fix = action.suggested_fix or ""
        expected_fix = ground_truth.get("fix", "")
        if predicted_fix and expected_fix:
            fix_quality_score = SequenceMatcher(None, predicted_fix, expected_fix).ratio()
        else:
            fix_quality_score = 0.0

        # 4. Explanation Quality Score
        explanation = (action.explanation or "").lower()
        keywords = ground_truth.get("keywords", [])
        if keywords and explanation:
            matches = sum(1 for kw in keywords if kw.lower() in explanation)
            explanation_quality_score = min(1.0, matches / len(keywords))
        else:
            explanation_quality_score = 0.0

        # 5. Investigation Efficiency Score
        optimal_steps = 3
        # history includes the current action
        investigation_efficiency_score = max(0.0, 1 - (len(history) - optimal_steps) * 0.2)
        if len(history) <= optimal_steps:
            investigation_efficiency_score = 1.0

        # Penalties
        false_positive_penalty = 0.0
        if predicted_lines and expected_lines:
            false_positives = predicted_lines - expected_lines
            false_positive_penalty = len(false_positives) * 0.1

        wrong_severity_penalty = 0.0
        if action.severity and ground_truth.get("severity"):
            if action.severity.value != ground_truth.get("severity").upper():
                wrong_severity_penalty = 0.05

        # Total Calculation
        total_reward = (
            0.25 * line_detection_score +
            0.20 * issue_classification_score +
            0.25 * fix_quality_score +
            0.15 * explanation_quality_score +
            0.15 * investigation_efficiency_score
        )
        
        # Apply penalties
        total_reward -= false_positive_penalty
        total_reward -= wrong_severity_penalty
        
        total_reward = max(0.0, min(1.0, total_reward))

        return RewardInfo(
            total_reward=total_reward,
            line_detection_score=line_detection_score,
            issue_classification_score=issue_classification_score,
            fix_quality_score=fix_quality_score,
            explanation_quality_score=explanation_quality_score,
            investigation_efficiency_score=investigation_efficiency_score,
            false_positive_penalty=false_positive_penalty,
            wrong_severity_penalty=wrong_severity_penalty,
            breakdown={
                "line_detection": line_detection_score,
                "issue_classification": issue_classification_score,
                "fix_quality": fix_quality_score,
                "explanation_quality": explanation_quality_score,
                "investigation_efficiency": investigation_efficiency_score
            },
            feedback=f"Score: {total_reward:.2f}. Detection: {line_detection_score:.2f}, Fix: {fix_quality_score:.2f}"
        )
