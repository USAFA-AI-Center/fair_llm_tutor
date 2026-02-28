"""Tests for student_mode/scenarios.py."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from student_mode.scenarios import Scenario, SCENARIOS, get_scenario, scenario_names


class TestScenarioData:
    """Verify all 17 built-in scenarios have valid structure."""

    def test_scenario_count(self):
        assert len(SCENARIOS) == 17

    def test_all_scenarios_have_required_fields(self):
        for name, s in SCENARIOS.items():
            assert s.topic, f"{name} missing topic"
            assert s.problem, f"{name} missing problem"
            assert s.initial_work, f"{name} missing initial_work"

    def test_all_scenarios_have_correct_answer(self):
        for name, s in SCENARIOS.items():
            assert s.correct_answer, f"{name} missing correct_answer"

    def test_all_scenarios_have_module(self):
        for name, s in SCENARIOS.items():
            assert s.module, f"{name} missing module"

    def test_all_scenarios_have_expected_behavior(self):
        valid_behaviors = {"hint_without_answer", "concept_explanation", "confirm_correct"}
        for name, s in SCENARIOS.items():
            assert s.expected_behavior in valid_behaviors, (
                f"{name} has invalid expected_behavior: {s.expected_behavior!r}"
            )

    def test_scenarios_are_frozen(self):
        s = SCENARIOS["derivatives"]
        with pytest.raises(AttributeError):
            s.topic = "modified"


class TestGetScenario:
    """Tests for get_scenario() lookup."""

    def test_valid_lookup(self):
        s = get_scenario("derivatives")
        assert s.topic == "calculus"

    def test_unknown_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown scenario"):
            get_scenario("nonexistent_scenario")

    def test_error_lists_available(self):
        with pytest.raises(KeyError, match="derivatives"):
            get_scenario("nonexistent_scenario")


class TestScenarioNames:
    """Tests for scenario_names() helper."""

    def test_returns_list(self):
        names = scenario_names()
        assert isinstance(names, list)

    def test_count_matches(self):
        assert len(scenario_names()) == len(SCENARIOS)

    def test_contains_known_names(self):
        names = scenario_names()
        assert "derivatives" in names
        assert "recursion" in names
        assert "economics_supply_demand" in names
