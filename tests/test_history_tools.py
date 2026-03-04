"""Tests for tools.history_tools — pure computation, no LLM needed."""

import json
from tools.history_tools import CheckStudentHistoryTool


class TestCheckStudentHistory:
    def setup_method(self):
        self.tool = CheckStudentHistoryTool()

    def test_no_match(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "x = 6",
            "student_history": ["I got x = 7", "Maybe x = 8?"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: NO" in result

    def test_exact_match(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "x = 6",
            "student_history": ["I think x = 6"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result
        assert "x = 6" in result

    def test_substring_match_answer_in_history(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "42",
            "student_history": ["I calculated 42 kg*m/s"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_substring_match_history_in_answer(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "The momentum is 42 kg*m/s",
            "student_history": ["42 kg*m/s"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_case_insensitive(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "George Washington",
            "student_history": ["george washington was the first president"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_empty_history(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "x = 6",
            "student_history": [],
        }))
        assert "STUDENT_ALREADY_ANSWERED: NO" in result

    def test_empty_correct_answer(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "",
            "student_history": ["some answer"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: NO" in result

    def test_invalid_json(self):
        result = self.tool.use("not json")
        assert "ERROR" in result

    def test_multiple_matches_reported(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "6",
            "student_history": ["I got 6", "Yes it's 6", "wrong answer"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result
        assert "I got 6" in result
        assert "Yes it's 6" in result
