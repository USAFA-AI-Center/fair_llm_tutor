"""Tests for eval/simulated_student.py."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM
from eval.scenarios import Scenario
from eval.simulated_student import SimulatedStudent, STUDENT_PROFILES


def _make_scenario(**overrides):
    defaults = dict(
        name="test",
        domain="math",
        problem="Solve 2x=10",
        correct_answer="x=5",
        student_profile="confused_beginner",
        student_work="x=3",
        expected_behavior="hint_without_answer",
    )
    defaults.update(overrides)
    return Scenario(**defaults)


class TestSimulatedStudent:
    def test_respond_returns_string(self):
        llm = MockLLM("I'm confused, is it x=4?")
        student = SimulatedStudent(llm, _make_scenario())
        reply = student.respond("Check your division step.")
        assert isinstance(reply, str)
        assert len(reply) > 0

    def test_respond_calls_llm(self):
        llm = MockLLM("OK let me try again")
        student = SimulatedStudent(llm, _make_scenario())
        student.respond("Think about what happens when you divide.")
        assert llm.call_count == 1

    def test_history_tracks_exchanges(self):
        llm = MockLLM("Hmm, maybe x=5?")
        student = SimulatedStudent(llm, _make_scenario())
        student.respond("First hint")
        student.respond("Second hint")
        assert len(student.history) == 4  # 2 tutor + 2 student entries
        assert "Tutor: First hint" in student.history
        assert "Tutor: Second hint" in student.history

    def test_profile_included_in_prompt(self):
        llm = MockLLM("response")
        student = SimulatedStudent(llm, _make_scenario(student_profile="adversarial"))
        student.respond("Try again.")
        prompt = llm.last_messages[0].content
        assert "reveal the answer" in prompt  # from adversarial profile

    def test_unknown_profile_falls_back(self):
        llm = MockLLM("response")
        student = SimulatedStudent(llm, _make_scenario(student_profile="unknown_type"))
        student.respond("Hint text")
        prompt = llm.last_messages[0].content
        assert "confused beginner" in prompt  # falls back to default

    def test_scenario_context_in_prompt(self):
        llm = MockLLM("response")
        scenario = _make_scenario(problem="Balance H2 + O2", student_work="H2O")
        student = SimulatedStudent(llm, scenario)
        student.respond("Check the hydrogen count.")
        prompt = llm.last_messages[0].content
        assert "Balance H2 + O2" in prompt
        assert "H2O" in prompt


class TestStudentProfiles:
    def test_all_profiles_exist(self):
        for profile in ["confused_beginner", "careless_expert", "adversarial"]:
            assert profile in STUDENT_PROFILES

    def test_profiles_are_nonempty(self):
        for desc in STUDENT_PROFILES.values():
            assert len(desc) > 20
