"""Tests for eval scenario loading."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.scenarios import Scenario, load_scenarios


class TestScenario:
    def test_scenario_fields(self):
        s = Scenario(
            name="test",
            domain="math",
            problem="Solve 2x=10",
            correct_answer="x=5",
            student_profile="confused_beginner",
            student_work="x=3",
            expected_behavior="hint_without_answer",
        )
        assert s.domain == "math"
        assert s.name == "test"
        assert s.student_profile == "confused_beginner"

    def test_load_scenarios_from_file(self, tmp_path):
        data = [
            {
                "name": "test1",
                "domain": "math",
                "problem": "Solve x+1=2",
                "correct_answer": "x=1",
                "student_profile": "confused_beginner",
                "student_work": "x=3",
                "expected_behavior": "hint_without_answer",
            }
        ]
        path = tmp_path / "scenarios.json"
        path.write_text(json.dumps(data))
        scenarios = load_scenarios(str(path))
        assert len(scenarios) == 1
        assert scenarios[0].name == "test1"

    def test_load_multiple_scenarios(self, tmp_path):
        data = [
            {
                "name": f"test{i}",
                "domain": "math",
                "problem": f"Problem {i}",
                "correct_answer": f"Answer {i}",
                "student_profile": "confused_beginner",
                "student_work": f"Work {i}",
                "expected_behavior": "hint_without_answer",
            }
            for i in range(5)
        ]
        path = tmp_path / "scenarios.json"
        path.write_text(json.dumps(data))
        scenarios = load_scenarios(str(path))
        assert len(scenarios) == 5

    def test_load_bundled_scenarios(self):
        """Verify the bundled scenarios.json loads correctly."""
        scenarios = load_scenarios("eval/scenarios.json")
        assert len(scenarios) >= 10
        domains = {s.domain for s in scenarios}
        assert len(domains) >= 4, f"Expected diverse domains, got: {domains}"
