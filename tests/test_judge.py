"""Tests for student_mode/judge.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM
from student_mode.judge import SessionJudge, JudgeScores, score_session, _is_work_turn


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


class TestSessionJudge:
    def test_score_turn_returns_judge_scores(self):
        response = json.dumps({
            "safety": 5, "pedagogy": 4, "helpfulness": 4,
            "domain_accuracy": 5, "reasoning": "Good Socratic hint"
        })
        llm = MockLLM(response)
        judge = SessionJudge(llm)
        scores = judge.score_turn(
            problem="Solve 2x=10",
            correct_answer="x=5",
            student_work="x=3",
            tutor_response="Check your division step.",
        )
        assert isinstance(scores, JudgeScores)
        assert scores.safety == 5
        assert scores.pedagogy == 4

    def test_score_turn_calls_llm(self):
        response = json.dumps({
            "safety": 3, "pedagogy": 3, "helpfulness": 3,
            "domain_accuracy": 3, "reasoning": "OK"
        })
        llm = MockLLM(response)
        judge = SessionJudge(llm)
        judge.score_turn(
            problem="Solve 2x=10",
            correct_answer="x=5",
            student_work="x=3",
            tutor_response="Try again.",
        )
        assert llm.call_count == 1

    def test_score_includes_problem_in_prompt(self):
        response = json.dumps({
            "safety": 3, "pedagogy": 3, "helpfulness": 3,
            "domain_accuracy": 3, "reasoning": "test"
        })
        llm = MockLLM(response)
        judge = SessionJudge(llm)
        judge.score_turn(
            problem="Balance H2 + O2",
            correct_answer="2H2 + O2 -> 2H2O",
            student_work="H2 + O2 = H2O",
            tutor_response="Hint text",
        )
        prompt = llm.last_messages[0].content
        assert "Balance H2 + O2" in prompt

    def test_fallback_on_invalid_json(self):
        llm = MockLLM("This is not valid JSON at all")
        judge = SessionJudge(llm)
        scores = judge.score_turn(
            problem="Solve 2x=10",
            correct_answer="x=5",
            student_work="x=3",
            tutor_response="Some hint",
        )
        assert scores.safety == 3
        assert scores.reasoning == "Parse failure"

    def test_fallback_on_missing_fields(self):
        llm = MockLLM('{"safety": 5}')  # Missing required fields
        judge = SessionJudge(llm)
        scores = judge.score_turn(
            problem="Solve 2x=10",
            correct_answer="x=5",
            student_work="x=3",
            tutor_response="Hint",
        )
        assert scores.safety == 3  # Falls back to defaults
        assert scores.reasoning == "Parse failure"


class TestIsWorkTurn:
    def test_setup_turns_excluded(self):
        assert not _is_work_turn({"student_input": "topic math", "tutor_response": "Topic set."})
        assert not _is_work_turn({"student_input": "problem Solve x=5", "tutor_response": "Problem set."})

    def test_teardown_excluded(self):
        assert not _is_work_turn({"student_input": "quit", "tutor_response": ""})
        assert not _is_work_turn({"student_input": "exit", "tutor_response": ""})

    def test_work_turn_included(self):
        assert _is_work_turn({"student_input": "I think x=3", "tutor_response": "Check your work."})

    def test_empty_response_excluded(self):
        assert not _is_work_turn({"student_input": "I think x=3", "tutor_response": ""})


class TestScoreSession:
    def test_scores_jsonl_file(self, tmp_path):
        """Write a minimal JSONL, verify score_session produces scored output."""
        jsonl_path = tmp_path / "test_session.jsonl"
        records = [
            {"session_id": "abc", "turn": 1, "student_input": "topic math",
             "tutor_response": "Topic set.", "latency_ms": 0, "module": "test"},
            {"session_id": "abc", "turn": 2, "student_input": "problem Solve 2x=10",
             "tutor_response": "Problem set.", "latency_ms": 0, "module": "test",
             "correct_answer": "x=5"},
            {"session_id": "abc", "turn": 3, "student_input": "I think x=3",
             "tutor_response": "Check your division.", "latency_ms": 1000, "module": "test"},
            {"session_id": "abc", "turn": 4, "student_input": "quit",
             "tutor_response": "", "latency_ms": 0, "module": "test"},
        ]
        with open(jsonl_path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        response = json.dumps({
            "safety": 5, "pedagogy": 4, "helpfulness": 4,
            "domain_accuracy": 5, "reasoning": "Good hint"
        })
        llm = MockLLM(response)
        judge = SessionJudge(llm)

        scored = score_session(judge, str(jsonl_path))

        # Only 1 work turn (turn 3) should be scored
        assert llm.call_count == 1
        scored_turns = [r for r in scored if "judge_scores" in r]
        assert len(scored_turns) == 1
        assert scored_turns[0]["judge_scores"]["safety"] == 5
        assert scored_turns[0]["quality_score"] == 4.5  # avg of 5,4,4,5

        # Output file should exist
        out_path = tmp_path / "test_session.scored.jsonl"
        assert out_path.exists()

    def test_raises_without_correct_answer(self, tmp_path):
        """Should raise if no correct_answer in JSONL or CLI."""
        jsonl_path = tmp_path / "no_answer.jsonl"
        records = [
            {"session_id": "abc", "turn": 1, "student_input": "I think x=3",
             "tutor_response": "Check your work.", "latency_ms": 1000, "module": "test"},
        ]
        with open(jsonl_path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        llm = MockLLM("{}")
        judge = SessionJudge(llm)

        with pytest.raises(ValueError, match="correct_answer"):
            score_session(judge, str(jsonl_path))

    def test_cli_correct_answer_override(self, tmp_path):
        """CLI --correct-answer should be used even if JSONL has one."""
        jsonl_path = tmp_path / "override.jsonl"
        records = [
            {"session_id": "abc", "turn": 1, "student_input": "problem Solve 2x=10",
             "tutor_response": "Problem set.", "latency_ms": 0, "module": "test",
             "correct_answer": "x=5"},
            {"session_id": "abc", "turn": 2, "student_input": "I think x=3",
             "tutor_response": "Check work.", "latency_ms": 1000, "module": "test"},
        ]
        with open(jsonl_path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        response = json.dumps({
            "safety": 5, "pedagogy": 5, "helpfulness": 5,
            "domain_accuracy": 5, "reasoning": "Perfect"
        })
        llm = MockLLM(response)
        judge = SessionJudge(llm)

        scored = score_session(judge, str(jsonl_path), correct_answer="x=5 override")

        # Verify the override answer was used in the prompt
        prompt = llm.last_messages[0].content
        assert "x=5 override" in prompt
