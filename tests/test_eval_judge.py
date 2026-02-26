"""Tests for eval/eval_judge.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM
from eval.scenarios import Scenario
from eval.eval_judge import EvalJudge, JudgeScores


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


class TestJudgeScores:
    def test_valid_scores(self):
        scores = JudgeScores(
            safety=5, pedagogy=4, helpfulness=3,
            domain_accuracy=5, reasoning="Good hint"
        )
        assert scores.safety == 5
        assert scores.reasoning == "Good hint"

    def test_from_dict(self):
        data = {
            "safety": 4, "pedagogy": 3, "helpfulness": 4,
            "domain_accuracy": 5, "reasoning": "Decent"
        }
        scores = JudgeScores(**data)
        assert scores.pedagogy == 3


class TestEvalJudge:
    def test_score_returns_judge_scores(self):
        response = json.dumps({
            "safety": 5, "pedagogy": 4, "helpfulness": 4,
            "domain_accuracy": 5, "reasoning": "Good Socratic hint"
        })
        llm = MockLLM(response)
        judge = EvalJudge(llm)
        scores = judge.score(_make_scenario(), "Check your division step.")
        assert isinstance(scores, JudgeScores)
        assert scores.safety == 5
        assert scores.pedagogy == 4

    def test_score_calls_llm(self):
        response = json.dumps({
            "safety": 3, "pedagogy": 3, "helpfulness": 3,
            "domain_accuracy": 3, "reasoning": "OK"
        })
        llm = MockLLM(response)
        judge = EvalJudge(llm)
        judge.score(_make_scenario(), "Try again.")
        assert llm.call_count == 1

    def test_score_includes_scenario_in_prompt(self):
        response = json.dumps({
            "safety": 3, "pedagogy": 3, "helpfulness": 3,
            "domain_accuracy": 3, "reasoning": "test"
        })
        llm = MockLLM(response)
        judge = EvalJudge(llm)
        scenario = _make_scenario(problem="Balance H2 + O2")
        judge.score(scenario, "Hint text")
        prompt = llm.last_messages[0].content
        assert "Balance H2 + O2" in prompt

    def test_fallback_on_invalid_json(self):
        llm = MockLLM("This is not valid JSON at all")
        judge = EvalJudge(llm)
        scores = judge.score(_make_scenario(), "Some hint")
        assert scores.safety == 3
        assert scores.reasoning == "Parse failure"

    def test_fallback_on_missing_fields(self):
        llm = MockLLM('{"safety": 5}')  # Missing required fields
        judge = EvalJudge(llm)
        scores = judge.score(_make_scenario(), "Hint")
        assert scores.safety == 3  # Falls back to defaults
        assert scores.reasoning == "Parse failure"
