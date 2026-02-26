"""Test scenario definitions for eval harness."""

import json
from dataclasses import dataclass
from typing import List


@dataclass
class Scenario:
    name: str
    domain: str
    problem: str
    correct_answer: str
    student_profile: str  # "confused_beginner", "careless_expert", "adversarial"
    student_work: str
    expected_behavior: str  # "hint_without_answer", "concept_explanation", "confirm_correct"


def load_scenarios(path: str) -> List[Scenario]:
    with open(path) as f:
        data = json.load(f)
    return [Scenario(**item) for item in data]
