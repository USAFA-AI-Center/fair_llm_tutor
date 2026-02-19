"""Tests for safety_tools.py — AnswerRevelationAnalyzerTool."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.safety_tools import AnswerRevelationAnalyzerTool
from tests.conftest import MockLLM, build_tool_input


class TestExtractStudentAnswersFromHistory:
    """Tests for _extract_student_answers_from_history."""

    def setup_method(self):
        self.tool = AnswerRevelationAnalyzerTool(llm=MockLLM())

    def test_empty_history_returns_empty(self):
        assert self.tool._extract_student_answers_from_history("") == []

    def test_empty_brackets_returns_empty(self):
        assert self.tool._extract_student_answers_from_history("[]") == []

    def test_none_returns_empty(self):
        assert self.tool._extract_student_answers_from_history(None) == []

    def test_extracts_answer_with_units(self):
        history = "['I calculated 50 kg m/s']"
        result = self.tool._extract_student_answers_from_history(history)
        assert len(result) >= 1

    def test_extracts_answer_with_keyword(self):
        history = "my answer is 42"
        result = self.tool._extract_student_answers_from_history(history)
        assert len(result) >= 1

    def test_no_answer_content_returns_empty(self):
        history = "hello"
        result = self.tool._extract_student_answers_from_history(history)
        assert result == []


class TestNormalizeAnswer:
    """Tests for _normalize_answer."""

    def setup_method(self):
        self.tool = AnswerRevelationAnalyzerTool(llm=MockLLM())

    def test_strips_whitespace(self):
        assert self.tool._normalize_answer("  50  ") == "50"

    def test_removes_multiplication_symbols(self):
        result = self.tool._normalize_answer("50*kg")
        assert "*" not in result

    def test_lowercases(self):
        result = self.tool._normalize_answer("50 KG")
        assert result == "50kg"

    def test_removes_spaces(self):
        result = self.tool._normalize_answer("50 kg m/s")
        assert " " not in result


class TestExtractVerdict:
    """Tests for _extract_verdict."""

    def setup_method(self):
        self.tool = AnswerRevelationAnalyzerTool(llm=MockLLM())

    def test_clear_safe_verdict(self):
        response = "VERDICT: SAFE\nREASONING: No answer revealed."
        assert self.tool._extract_verdict(response, False) == "SAFE"

    def test_clear_unsafe_verdict(self):
        response = "VERDICT: UNSAFE\nREASONING: Answer was given directly."
        assert self.tool._extract_verdict(response, False) == "UNSAFE"

    def test_garbled_text_defaults_to_unsafe(self):
        """After bug fix, unclear verdict should default to UNSAFE (conservative)."""
        response = "I'm not sure what to say here. The response is ambiguous."
        assert self.tool._extract_verdict(response, False) == "UNSAFE"

    def test_unsafe_overridden_when_student_already_answered(self):
        response = "VERDICT: UNSAFE\nREASONING: The response confirms the correct answer."
        result = self.tool._extract_verdict(response, student_already_answered=True)
        assert result == "SAFE"

    def test_student_already_answered_with_confirm_phrase(self):
        response = "That's correct! Well done."
        result = self.tool._extract_verdict(response, student_already_answered=True)
        assert result == "SAFE"

    def test_student_not_answered_with_unsafe_mention(self):
        response = "This seems UNSAFE because it reveals the calculation."
        result = self.tool._extract_verdict(response, student_already_answered=False)
        assert result == "UNSAFE"


class TestAnswerRevelationAnalyzerUse:
    """Tests for the main use() method."""

    def test_parses_all_four_fields(self):
        """Verify label-based parsing works for all 4 fields (bug fix 1A)."""
        llm = MockLLM("VERDICT: SAFE\nREASONING: OK")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_tool_input(
            PROBLEM="Find derivative of x^2",
            CORRECT_ANSWER="2x",
            STUDENT_HISTORY="[]",
            PROPOSED_RESPONSE="Think about the power rule."
        )

        result = tool.use(tool_input)
        assert "SAFE" in result

    def test_student_not_answered_with_answer_in_response(self):
        """When student hasn't answered and response reveals answer, should be UNSAFE."""
        llm = MockLLM("VERDICT: UNSAFE\nREASONING: Response states the answer directly.")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_tool_input(
            PROBLEM="What is 5 * 10?",
            CORRECT_ANSWER="50",
            STUDENT_HISTORY="[]",
            PROPOSED_RESPONSE="The answer is 50."
        )

        result = tool.use(tool_input)
        assert "UNSAFE" in result

    def test_student_already_answered_correctly(self):
        """When student already gave correct answer, confirming should be SAFE."""
        llm = MockLLM("VERDICT: SAFE\nREASONING: Student already gave this answer.")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_tool_input(
            PROBLEM="Calculate momentum of 5kg at 10m/s",
            CORRECT_ANSWER="50 kg m/s",
            STUDENT_HISTORY="['my answer is 50 kg m/s']",
            PROPOSED_RESPONSE="Excellent! Your answer of 50 kg*m/s is correct!"
        )

        result = tool.use(tool_input)
        assert "SAFE" in result

    def test_handles_missing_fields_gracefully(self):
        """Tool should not crash if some fields are missing."""
        llm = MockLLM("VERDICT: SAFE\nREASONING: OK")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        result = tool.use("PROBLEM: some problem")
        # Should not crash, should still return something
        assert isinstance(result, str)

    def test_no_double_parsing_bug(self):
        """Verify the double-parsing bug (lines 116-118) is fixed.

        Previously, positional indexing overwrote label-based parsing,
        causing parts[2] (STUDENT_HISTORY) to be used as PROPOSED_RESPONSE.
        """
        llm = MockLLM("VERDICT: UNSAFE\nREASONING: Response gives answer.")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        # With 4 fields, parts[2] is STUDENT_HISTORY, not PROPOSED_RESPONSE
        tool_input = (
            "PROBLEM: What is 2+2? ||| "
            "CORRECT_ANSWER: 4 ||| "
            "STUDENT_HISTORY: [I think it might be 3] ||| "
            "PROPOSED_RESPONSE: The answer is 4!"
        )

        result = tool.use(tool_input)
        # The LLM should have received the actual proposed_response, not student_history
        prompt_sent = llm.last_messages[0].content
        assert "The answer is 4!" in prompt_sent
        assert "PROPOSED RESPONSE TO VALIDATE: The answer is 4!" in prompt_sent
