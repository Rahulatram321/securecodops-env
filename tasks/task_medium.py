import json
import random
import os

class MediumTask:
    task_id = "security_audit"
    difficulty = "medium"
    description = "Identify security vulnerabilities based on real CVE patterns"
    max_steps = 7

    def __init__(self):
        dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "medium_samples.json")
        with open(dataset_path, "r") as f:
            self.samples = json.load(f)

    def get_sample(self) -> dict:
        return random.choice(self.samples)

    def get_action_schema(self) -> dict:
        return {
            "required": ["action_type", "line_numbers", "issue_type", "severity", "suggested_fix"],
            "recommended_action": "IDENTIFY_ISSUE"
        }
