import difflib
from typing import Dict, Any, List
from .models import Action, ActionType

class RewardInfo:
    def __init__(self):
        self.total_reward: float = 0.0
        self.line_detection_score: float = 0.0
        self.issue_classification_score: float = 0.0
        self.fix_quality_score: float = 0.0
        self.explanation_quality_score: float = 0.0
        self.investigation_efficiency_score: float = 0.0
        self.penalties: float = 0.0
        self.feedback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_reward": round(float(self.total_reward), 4),
            "components": {
                "line_detection": round(float(self.line_detection_score), 4),
                "issue_classification": round(float(self.issue_classification_score), 4),
                "fix_quality": round(float(self.fix_quality_score), 4),
                "explanation_quality": round(float(self.explanation_quality_score), 4),
                "investigation_efficiency": round(float(self.investigation_efficiency_score), 4)
            },
            "penalties": round(float(self.penalties), 4),
            "feedback": self.feedback
        }

class RewardCalculator:
    def calculate(self, action: Action, ground_truth: Dict[str, Any], task_id: str, history: List[Any]) -> RewardInfo:
        info = RewardInfo()
        
        # Improvement 3: Handle Missing Ground Truth
        if not ground_truth or not isinstance(ground_truth, dict):
            info.feedback = "Missing or invalid ground truth data."
            return info

        # 1. Line Detection Score (0.25)
        # Improvement 4 & 7: Fix Edge Case and Numerical Stability
        # ---------------------------------------------------------------------
        expected_lines = set(ground_truth.get("lines", []))
        predicted_lines = set(action.line_numbers or [])
        
        if not expected_lines:
            # Score 1.0 ONLY IF no lines predicted, else 0.0
            info.line_detection_score = 1.0 if not predicted_lines else 0.0
        else:
            if not predicted_lines:
                info.line_detection_score = 0.0
            else:
                intersection = predicted_lines.intersection(expected_lines)
                info.line_detection_score = len(intersection) / len(expected_lines)
        
        # Improvement 5: Clamp
        info.line_detection_score = max(0.0, min(1.0, info.line_detection_score))

        # 2. Issue Classification Score (0.20)
        # Improvement 1 & 2: Safe Enum Access and Safe Normalization
        # ---------------------------------------------------------------------
        gt_type = str(ground_truth.get("type", "")).strip().lower()
        pred_type = str(action.issue_type.value if action.issue_type else "").strip().lower()
        
        if not action.issue_type:
            info.issue_classification_score = 0.0
        elif pred_type == gt_type:
            info.issue_classification_score = 1.0
        elif (pred_type == "bug" and gt_type == "logic") or (pred_type == "security" and gt_type == "security"):
            info.issue_classification_score = 0.5
        else:
            info.issue_classification_score = 0.0
            
        # Improvement 5: Clamp
        info.issue_classification_score = max(0.0, min(1.0, info.issue_classification_score))

        # 3. Fix Quality Score (0.25)
        # Improvement 7: Numerical Stability
        # ---------------------------------------------------------------------
        predicted_fix = str(action.suggested_fix or "").strip()
        expected_fix = str(ground_truth.get("fix", "")).strip()
        
        if not predicted_fix or not expected_fix:
            info.fix_quality_score = 0.0
        else:
            sm = difflib.SequenceMatcher(None, predicted_fix, expected_fix)
            info.fix_quality_score = float(sm.ratio())
            
        # Improvement 5: Clamp
        info.fix_quality_score = max(0.0, min(1.0, info.fix_quality_score))

        # 4. Explanation Quality Score (0.15)
        # ---------------------------------------------------------------------
        explanation = str(action.explanation or "").strip().lower()
        keywords = [str(k).strip().lower() for k in ground_truth.get("keywords", []) if k]
        
        if not keywords:
            info.explanation_quality_score = 0.5
        else:
            matches = sum(1 for k in keywords if k in explanation)
            info.explanation_quality_score = min(1.0, matches / len(keywords))
            
        # Improvement 5: Clamp
        info.explanation_quality_score = max(0.0, min(1.0, info.explanation_quality_score))

        # 5. Investigation Efficiency Score (0.15)
        # ---------------------------------------------------------------------
        optimal_steps = 3
        history_len = len(history)
        if history_len <= optimal_steps:
            info.investigation_efficiency_score = 1.0
        else:
            # Prevent negative score before clamping
            raw_efficiency = 1.0 - (history_len - optimal_steps) * 0.2
            info.investigation_efficiency_score = max(0.0, raw_efficiency)
            
        # Improvement 5: Clamp
        info.investigation_efficiency_score = max(0.0, min(1.0, info.investigation_efficiency_score))

        # Penalties
        # ---------------------------------------------------------------------
        # False Positive Penalty: -0.1 per wrong line
        false_positives = predicted_lines - expected_lines
        info.penalties += len(false_positives) * 0.1

        # Improvement 1 & 2: Safe Enum and Normalization for Severity
        if action.severity and ground_truth.get("severity"):
            pred_severity = str(action.severity.value if action.severity else "").strip().lower()
            gt_severity = str(ground_truth.get("severity", "")).strip().lower()
            if pred_severity and gt_severity and pred_severity != gt_severity:
                info.penalties += 0.05

        # Final Reward Calculation
        # Improvement 6: Final Reward Clamp
        # ---------------------------------------------------------------------
        raw_total = (
            0.25 * info.line_detection_score +
            0.20 * info.issue_classification_score +
            0.25 * info.fix_quality_score +
            0.15 * info.explanation_quality_score +
            0.15 * info.investigation_efficiency_score
        )
        
        info.total_reward = max(0.0, min(1.0, raw_total - info.penalties))
        
        # Build Feedback
        if info.total_reward > 0.8:
            info.feedback = "Excellent investigation and fix."
        elif info.total_reward > 0.4:
            info.feedback = "Partial success. Refine line detection or fix accuracy."
        else:
            info.feedback = "Significant issues detected in the investigation trajectory."
            
        return info
