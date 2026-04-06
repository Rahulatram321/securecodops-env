import difflib
from typing import Dict, Any, List
from .models import Action, ActionType, RewardInfo as RewardInfoModel

class RewardCalculator:
    def calculate(self, action: Action, ground_truth: Dict[str, Any], task_id: str, history: List[Any]) -> RewardInfoModel:
        # Default scaffold
        info_kwargs = {
            "total_reward": 0.0,
            "line_detection_score": 0.0,
            "issue_classification_score": 0.0,
            "fix_quality_score": 0.0,
            "explanation_quality_score": 0.0,
            "investigation_efficiency_score": 0.0,
            "false_positive_penalty": 0.0,
            "irrelevant_request_penalty": 0.0,
            "wrong_severity_penalty": 0.0,
            "breakdown": {},
            "feedback": "Missing or invalid ground truth data."
        }

        if not ground_truth or not isinstance(ground_truth, dict):
            return RewardInfoModel(**info_kwargs)

        # 1. Line Detection Score (0.25)
        # Improvement 4 & 7: Fix Edge Case and Numerical Stability
        # ---------------------------------------------------------------------
        expected_lines = set(ground_truth.get("lines", []))
        predicted_lines = set(action.line_numbers or [])
        
        if not expected_lines:
            info_kwargs["line_detection_score"] = 1.0 if not predicted_lines else 0.0
        else:
            if not predicted_lines:
                info_kwargs["line_detection_score"] = 0.0
            else:
                intersection = predicted_lines.intersection(expected_lines)
                info_kwargs["line_detection_score"] = len(intersection) / len(expected_lines)
        
        info_kwargs["line_detection_score"] = max(0.0, min(1.0, info_kwargs["line_detection_score"]))

        # 2. Issue Classification Score (0.20)
        # Improvement 1 & 2: Safe Enum Access and Safe Normalization
        # ---------------------------------------------------------------------
        gt_type = str(ground_truth.get("type", "")).strip().lower()
        pred_type = str(action.issue_type.value if action.issue_type else "").strip().lower()
        
        if not action.issue_type:
            info_kwargs["issue_classification_score"] = 0.0
        elif pred_type == gt_type:
            info_kwargs["issue_classification_score"] = 1.0
        elif (pred_type == "bug" and gt_type == "logic") or (pred_type == "security" and gt_type == "security"):
            info_kwargs["issue_classification_score"] = 0.5
        else:
            info_kwargs["issue_classification_score"] = 0.0
        info_kwargs["issue_classification_score"] = max(0.0, min(1.0, info_kwargs["issue_classification_score"]))

        # 3. Fix Quality Score (0.25)
        # Improvement 7: Numerical Stability
        # ---------------------------------------------------------------------
        predicted_fix = str(action.suggested_fix or "").strip()
        expected_fix = str(ground_truth.get("fix", "")).strip()
        
        if not predicted_fix or not expected_fix:
            info_kwargs["fix_quality_score"] = 0.0
        else:
            sm = difflib.SequenceMatcher(None, predicted_fix, expected_fix)
            info_kwargs["fix_quality_score"] = float(sm.ratio())
        info_kwargs["fix_quality_score"] = max(0.0, min(1.0, info_kwargs["fix_quality_score"]))

        # 4. Explanation Quality Score (0.15)
        # ---------------------------------------------------------------------
        explanation = str(action.explanation or "").strip().lower()
        keywords = [str(k).strip().lower() for k in ground_truth.get("keywords", []) if k]
        
        if not keywords:
            info_kwargs["explanation_quality_score"] = 0.5
        else:
            matches = sum(1 for k in keywords if k in explanation)
            info_kwargs["explanation_quality_score"] = min(1.0, matches / len(keywords))
        info_kwargs["explanation_quality_score"] = max(0.0, min(1.0, info_kwargs["explanation_quality_score"]))

        # 5. Investigation Efficiency Score (0.15)
        # ---------------------------------------------------------------------
        optimal_steps = 3
        history_len = len(history)
        if history_len <= optimal_steps:
            info_kwargs["investigation_efficiency_score"] = 1.0
        else:
            raw_efficiency = 1.0 - (history_len - optimal_steps) * 0.2
            info_kwargs["investigation_efficiency_score"] = max(0.0, raw_efficiency)
        info_kwargs["investigation_efficiency_score"] = max(0.0, min(1.0, info_kwargs["investigation_efficiency_score"]))

        # Penalties
        # ---------------------------------------------------------------------
        # False Positive Penalty: -0.1 per wrong line
        false_positives = predicted_lines - expected_lines
        info_kwargs["false_positive_penalty"] = len(false_positives) * 0.1

        # Improvement 1 & 2: Safe Enum and Normalization for Severity
        if action.severity and ground_truth.get("severity"):
            pred_severity = str(action.severity.value if action.severity else "").strip().lower()
            gt_severity = str(ground_truth.get("severity", "")).strip().lower()
            if pred_severity and gt_severity and pred_severity != gt_severity:
                info_kwargs["wrong_severity_penalty"] = 0.05

        # Final Reward Calculation
        # Improvement 6: Final Reward Clamp
        # ---------------------------------------------------------------------
        raw_total = (
            0.25 * info_kwargs["line_detection_score"] +
            0.20 * info_kwargs["issue_classification_score"] +
            0.25 * info_kwargs["fix_quality_score"] +
            0.15 * info_kwargs["explanation_quality_score"] +
            0.15 * info_kwargs["investigation_efficiency_score"]
        )
        total_penalties = info_kwargs["false_positive_penalty"] + info_kwargs["wrong_severity_penalty"]
        info_kwargs["breakdown"] = {
            "line_detection": info_kwargs["line_detection_score"],
            "issue_classification": info_kwargs["issue_classification_score"],
            "fix_quality": info_kwargs["fix_quality_score"],
            "explanation_quality": info_kwargs["explanation_quality_score"],
            "investigation_efficiency": info_kwargs["investigation_efficiency_score"],
            "penalties": total_penalties
        }
        info_kwargs["total_reward"] = max(0.0, min(1.0, raw_total - total_penalties))
        
        # Build Feedback
        if info_kwargs["total_reward"] > 0.8:
            info_kwargs["feedback"] = "Excellent investigation and fix."
        elif info_kwargs["total_reward"] > 0.4:
            info_kwargs["feedback"] = "Partial success. Refine line detection or fix accuracy."
        else:
            info_kwargs["feedback"] = "Significant issues detected in the investigation trajectory."

        return RewardInfoModel(**info_kwargs)
