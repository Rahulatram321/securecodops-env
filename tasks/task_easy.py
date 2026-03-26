import json
import random
import os

class EasyTask:
    task_id = "spot_the_bug"
    difficulty = "easy"
    description = "Identify obvious bugs in single-function code snippets"
    max_steps = 5

    def __init__(self):
        dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "easy_samples.json")
        with open(dataset_path, "r") as f:
            self.samples = json.load(f)

    def get_sample(self) -> dict:
        return random.choice(self.samples)

    def get_action_schema(self) -> dict:
        return {
            "required": ["action_type", "line_numbers", "issue_type", "severity", "explanation"],
            "recommended_action": "IDENTIFY_ISSUE"
        }
