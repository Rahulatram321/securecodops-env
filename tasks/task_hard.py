import json
import random
import os
from env.models import Phase, ActionType, Action

class HardTask:
    task_id = "system_debug"
    difficulty = "hard"
    description = "Multi-turn system debugging using logs, stack traces, multi-file"
    max_steps = 10

    ALLOWED_ACTIONS = {
        Phase.INIT: [ActionType.REQUEST_FILE, ActionType.ASK_QUESTION, ActionType.FORM_HYPOTHESIS],
        Phase.CONTEXT_FETCH: [ActionType.REQUEST_FILE, ActionType.NARROW_DOWN, ActionType.FORM_HYPOTHESIS],
        Phase.ROOT_CAUSE: [ActionType.PROPOSE_FIX, ActionType.IDENTIFY_ISSUE],
        Phase.FINAL: [ActionType.PROPOSE_FIX]
    }

    def __init__(self):
        dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "hard_samples.json")
        with open(dataset_path, "r") as f:
            self.samples = json.load(f)

    def get_sample(self) -> dict:
        return random.choice(self.samples)

    def get_next_phase(self, current_phase: Phase, action: Action) -> Phase:
        if current_phase == Phase.INIT:
            if action.action_type == ActionType.REQUEST_FILE:
                return Phase.CONTEXT_FETCH
            elif action.action_type == ActionType.FORM_HYPOTHESIS:
                return Phase.ROOT_CAUSE
            elif action.action_type == ActionType.ASK_QUESTION:
                return Phase.INIT
        elif current_phase == Phase.CONTEXT_FETCH:
            if action.action_type == ActionType.NARROW_DOWN:
                return Phase.ROOT_CAUSE
            elif action.action_type == ActionType.REQUEST_FILE:
                return Phase.CONTEXT_FETCH
            elif action.action_type == ActionType.FORM_HYPOTHESIS:
                return Phase.ROOT_CAUSE
        elif current_phase == Phase.ROOT_CAUSE:
            if action.action_type == ActionType.PROPOSE_FIX or action.action_type == ActionType.IDENTIFY_ISSUE:
                return Phase.FINAL
        elif current_phase == Phase.FINAL:
            return Phase.FINAL
        
        return current_phase

    def get_action_schema(self) -> dict:
        return {
            "phases": {p.value: [a.value for a in actions] for p, actions in self.ALLOWED_ACTIONS.items()},
            "required_for_final": ["action_type", "suggested_fix", "explanation"]
        }
