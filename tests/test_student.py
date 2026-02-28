"""Tests for student_mode/student.py."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from student_mode.student import (
    build_student_llm,
    generate_response_deterministic,
    generate_response_llm,
)
from tests.conftest import MockLLM


class TestBuildStudentLLM:
    """Tests for build_student_llm() provider dispatch."""

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown student LLM provider"):
            build_student_llm("fake_provider")


class TestGenerateResponseDeterministic:
    """Tests for the canned-response generator."""

    def test_first_turn_returns_initial_work(self):
        result = generate_response_deterministic(
            tutor_response="",
            problem="Solve 2x=10",
            history=[],
            initial_work="I got x=3",
        )
        assert result == "I got x=3"

    def test_first_turn_without_initial_work(self):
        """Without initial_work, first turn returns a canned response."""
        result = generate_response_deterministic(
            tutor_response="Try again.",
            problem="Solve 2x=10",
            history=[],
            initial_work="",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_subsequent_turn_returns_canned_response(self):
        history = [
            {"student_input": "I got x=3", "tutor_response": "Check division."},
        ]
        result = generate_response_deterministic(
            tutor_response="Check division.",
            problem="Solve 2x=10",
            history=history,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_setup_turns_excluded_from_work_count(self):
        """Setup commands (topic, problem) don't count as work turns."""
        history = [
            {"student_input": "topic math", "tutor_response": "Topic set."},
            {"student_input": "problem Solve 2x=10", "tutor_response": "Problem set."},
        ]
        result = generate_response_deterministic(
            tutor_response="Problem set.",
            problem="Solve 2x=10",
            history=history,
            initial_work="x=3",
        )
        # Setup turns don't count, so this is still the "first" work turn
        assert result == "x=3"

    def test_quit_turns_excluded_from_work_count(self):
        history = [
            {"student_input": "quit", "tutor_response": ""},
        ]
        result = generate_response_deterministic(
            tutor_response="",
            problem="Solve 2x=10",
            history=history,
            initial_work="x=3",
        )
        assert result == "x=3"


class TestGenerateResponseLLM:
    """Tests for the LLM-driven generator."""

    def test_first_turn_returns_initial_work(self):
        llm = MockLLM("I should not be called")
        result = generate_response_llm(
            llm=llm,
            tutor_response="",
            problem="Solve 2x=10",
            history=[],
            initial_work="I got x=3",
        )
        assert result == "I got x=3"
        assert llm.call_count == 0

    def test_subsequent_turn_calls_llm(self):
        llm = MockLLM("Let me try x=5 instead.")
        history = [
            {"student_input": "I got x=3", "tutor_response": "Check your division."},
        ]
        result = generate_response_llm(
            llm=llm,
            tutor_response="Check your division.",
            problem="Solve 2x=10",
            history=history,
        )
        assert result == "Let me try x=5 instead."
        assert llm.call_count == 1

    def test_prompt_includes_problem(self):
        llm = MockLLM("OK")
        history = [
            {"student_input": "I got x=3", "tutor_response": "Hint."},
        ]
        generate_response_llm(
            llm=llm,
            tutor_response="Hint.",
            problem="Solve 2x=10",
            history=history,
        )
        prompt = llm.last_messages[0].content
        assert "Solve 2x=10" in prompt

    def test_prompt_includes_tutor_response(self):
        llm = MockLLM("OK")
        history = [
            {"student_input": "I got x=3", "tutor_response": "Check division step."},
        ]
        generate_response_llm(
            llm=llm,
            tutor_response="Check division step.",
            problem="Solve 2x=10",
            history=history,
        )
        prompt = llm.last_messages[0].content
        assert "Check division step." in prompt
