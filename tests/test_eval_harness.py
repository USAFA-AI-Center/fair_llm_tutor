"""Tests for eval/eval_harness.py."""

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM
from eval.eval_config import EvalConfig
from eval.scenarios import Scenario
from eval.eval_harness import EvalHarness, ConversationResult, EvalReport
from eval.eval_judge import JudgeScores


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


class TestConversationResult:
    def test_avg_score(self):
        scores = [
            JudgeScores(safety=5, pedagogy=4, helpfulness=3, domain_accuracy=5, reasoning="a"),
            JudgeScores(safety=3, pedagogy=2, helpfulness=5, domain_accuracy=3, reasoning="b"),
        ]
        result = ConversationResult(scenario_name="test", turns=[], scores=scores)
        assert result.avg_score("safety") == 4.0
        assert result.avg_score("helpfulness") == 4.0

    def test_avg_score_empty(self):
        result = ConversationResult(scenario_name="test", turns=[], scores=[])
        assert result.avg_score("safety") == 0.0

    def test_to_dict(self):
        scores = [JudgeScores(safety=5, pedagogy=4, helpfulness=3, domain_accuracy=5, reasoning="ok")]
        result = ConversationResult(scenario_name="test", turns=[{"turn": 1}], scores=scores)
        d = result.to_dict()
        assert d["scenario_name"] == "test"
        assert "avg_safety" in d
        assert d["avg_safety"] == 5.0


class TestEvalReport:
    def test_aggregate(self):
        scores1 = [JudgeScores(safety=5, pedagogy=4, helpfulness=4, domain_accuracy=5, reasoning="a")]
        scores2 = [JudgeScores(safety=3, pedagogy=2, helpfulness=2, domain_accuracy=3, reasoning="b")]
        results = [
            ConversationResult(scenario_name="s1", turns=[], scores=scores1),
            ConversationResult(scenario_name="s2", turns=[], scores=scores2),
        ]
        report = EvalReport(results=results)
        agg = report.aggregate()
        assert agg["safety"] == 4.0
        assert agg["pedagogy"] == 3.0

    def test_aggregate_empty(self):
        report = EvalReport(results=[])
        agg = report.aggregate()
        assert agg["safety"] == 0

    def test_to_dict(self):
        report = EvalReport(results=[])
        d = report.to_dict()
        assert "aggregate" in d
        assert "conversations" in d
        assert d["num_scenarios"] == 0


class TestEvalHarness:
    def test_run_scenario_produces_result(self):
        """Single scenario produces ConversationResult with correct turns."""
        judge_response = json.dumps({
            "safety": 5, "pedagogy": 4, "helpfulness": 4,
            "domain_accuracy": 5, "reasoning": "Good hint"
        })

        async def mock_tutor_fn(problem, student_work, topic):
            return "Check your division step."

        config = EvalConfig(max_turns_per_conversation=2)
        harness = EvalHarness(
            config=config,
            tutor_fn=mock_tutor_fn,
            student_llm=MockLLM("Let me try again: x=5"),
            judge_llm=MockLLM(judge_response),
        )

        scenario = _make_scenario()
        result = asyncio.run(harness.run_scenario(scenario))
        assert isinstance(result, ConversationResult)
        assert len(result.turns) == 2
        assert len(result.scores) == 2
        assert result.turns[0]["student"] == "x=3"  # Initial work
        assert result.turns[0]["tutor"] == "Check your division step."

    def test_run_multiple_scenarios(self):
        """Full run with multiple scenarios."""
        judge_response = json.dumps({
            "safety": 4, "pedagogy": 3, "helpfulness": 3,
            "domain_accuracy": 4, "reasoning": "OK"
        })

        async def mock_tutor_fn(problem, student_work, topic):
            return "Hint text"

        config = EvalConfig(max_turns_per_conversation=1)
        harness = EvalHarness(
            config=config,
            tutor_fn=mock_tutor_fn,
            student_llm=MockLLM("response"),
            judge_llm=MockLLM(judge_response),
        )

        scenarios = [_make_scenario(name="s1"), _make_scenario(name="s2")]
        report = asyncio.run(harness.run(scenarios))
        assert isinstance(report, EvalReport)
        assert len(report.results) == 2
        agg = report.aggregate()
        assert agg["safety"] == 4.0

    def test_tutor_fn_receives_correct_args(self):
        """Verify tutor_fn is called with scenario problem/work/domain."""
        calls = []

        async def tracking_tutor_fn(problem, student_work, topic):
            calls.append((problem, student_work, topic))
            return "Response"

        judge_response = json.dumps({
            "safety": 3, "pedagogy": 3, "helpfulness": 3,
            "domain_accuracy": 3, "reasoning": "ok"
        })
        config = EvalConfig(max_turns_per_conversation=1)
        harness = EvalHarness(
            config=config,
            tutor_fn=tracking_tutor_fn,
            student_llm=MockLLM("reply"),
            judge_llm=MockLLM(judge_response),
        )

        scenario = _make_scenario(problem="Solve x+1=2", domain="algebra")
        asyncio.run(harness.run_scenario(scenario))
        assert len(calls) == 1
        assert calls[0][0] == "Solve x+1=2"
        assert calls[0][2] == "algebra"
