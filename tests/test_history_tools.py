"""Tests for tools.history_tools — pure computation, no LLM needed."""

import json
from tools.history_tools import CheckStudentHistoryTool, _normalize_math


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


class TestMathAwareMatching:
    """Tests for math-aware normalization and matching."""

    def setup_method(self):
        self.tool = CheckStudentHistoryTool()

    def test_whitespace_around_operators(self):
        """'6x + 2' should match '6x+2'."""
        result = self.tool.use(json.dumps({
            "correct_answer": "6x + 2",
            "student_history": ["I got 6x+2"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_prefix_stripping_fprime(self):
        """'f'(x) = 6x + 2' should match '6x+2'."""
        result = self.tool.use(json.dumps({
            "correct_answer": "f'(x) = 6x + 2",
            "student_history": ["6x+2"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_prefix_stripping_the_answer_is(self):
        """'the answer is 42' should match '42'."""
        result = self.tool.use(json.dumps({
            "correct_answer": "42",
            "student_history": ["the answer is 42"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_numeric_comparison_integers(self):
        """'50' should match '50.0'."""
        result = self.tool.use(json.dumps({
            "correct_answer": "50",
            "student_history": ["I got 50.0"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_numeric_comparison_floats(self):
        """'3.14' should match '3.14'."""
        result = self.tool.use(json.dumps({
            "correct_answer": "3.14",
            "student_history": ["3.14"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_commutative_not_matched_by_default(self):
        """'2 + 6x' should NOT match '6x + 2' via substring (no algebraic CAS)."""
        result = self.tool.use(json.dumps({
            "correct_answer": "6x + 2",
            "student_history": ["2 + 6x"],
        }))
        # This won't match because normalized strings differ
        assert "STUDENT_ALREADY_ANSWERED: NO" in result

    def test_x_equals_prefix_stripped(self):
        """'x = 6' should match 'I got 6' via normalization."""
        result = self.tool.use(json.dumps({
            "correct_answer": "x = 6",
            "student_history": ["I got 6"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result


class TestNewPrefixPatterns:
    """Tests for newly added answer prefix patterns."""

    def setup_method(self):
        self.tool = CheckStudentHistoryTool()

    def test_i_believe_prefix(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "42",
            "student_history": ["i believe 42"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_it_should_be_prefix(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "42",
            "student_history": ["it should be 42"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_the_result_is_prefix(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "42",
            "student_history": ["the result is 42"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_i_calculated_prefix(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "42",
            "student_history": ["i calculated 42"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_the_solution_is_prefix(self):
        result = self.tool.use(json.dumps({
            "correct_answer": "42",
            "student_history": ["the solution is 42"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result


class TestEpsilonComparison:
    """Tests for configurable epsilon in numeric comparison."""

    def test_default_epsilon_is_forgiving(self):
        """0.333 vs 0.33333 should match with default epsilon of 1e-4."""
        tool = CheckStudentHistoryTool()
        result = tool.use(json.dumps({
            "correct_answer": "0.33333",
            "student_history": ["0.3333"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: YES" in result

    def test_custom_epsilon(self):
        """Custom tight epsilon should reject near-miss."""
        tool = CheckStudentHistoryTool(epsilon=1e-8)
        result = tool.use(json.dumps({
            "correct_answer": "0.33333",
            "student_history": ["0.3333"],
        }))
        assert "STUDENT_ALREADY_ANSWERED: NO" in result


class TestNormalizeMath:
    """Unit tests for the normalization helper."""

    def test_strips_whitespace_around_operators(self):
        assert _normalize_math("6x + 2") == "6x+2"

    def test_strips_fprime_prefix(self):
        assert _normalize_math("f'(x) = 6x + 2") == "6x+2"

    def test_strips_the_answer_is(self):
        assert _normalize_math("the answer is 42") == "42"

    def test_strips_i_got(self):
        assert _normalize_math("I got 15") == "15"

    def test_preserves_non_prefixed(self):
        assert _normalize_math("50 kg*m/s") == "50 kg*m/s"
