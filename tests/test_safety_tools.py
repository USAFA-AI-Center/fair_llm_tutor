"""Tests for safety_tools.py — AnswerRevelationAnalyzerTool."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.safety_tools import AnswerRevelationAnalyzerTool
from tools.schemas import SafetyInput
from tests.conftest import MockLLM, build_json_input


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

    def test_parses_json_input(self):
        llm = MockLLM("VERDICT: SAFE\nREASONING: OK")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_json_input(
            SafetyInput,
            problem="Find derivative of x^2",
            correct_answer="2x",
            student_history=[],
            proposed_response="Think about the power rule."
        )

        result = tool.use(tool_input)
        assert "SAFE" in result

    def test_student_not_answered_with_answer_in_response(self):
        """When student hasn't answered and response reveals answer, should be UNSAFE."""
        llm = MockLLM("VERDICT: UNSAFE\nREASONING: Response states the answer directly.")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_json_input(
            SafetyInput,
            problem="What is 5 * 10?",
            correct_answer="50",
            student_history=[],
            proposed_response="The answer is 50."
        )

        result = tool.use(tool_input)
        assert "UNSAFE" in result

    def test_student_already_answered_correctly(self):
        """When student already gave correct answer, confirming should be SAFE."""
        llm = MockLLM("VERDICT: SAFE\nREASONING: Student already gave this answer.")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_json_input(
            SafetyInput,
            problem="Calculate momentum of 5kg at 10m/s",
            correct_answer="50 kg m/s",
            student_history=["my answer is 50 kg m/s"],
            proposed_response="Excellent! Your answer of 50 kg*m/s is correct!"
        )

        result = tool.use(tool_input)
        assert "SAFE" in result

    def test_invalid_json_returns_error(self):
        llm = MockLLM("VERDICT: SAFE\nREASONING: OK")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        result = tool.use("not valid json")
        assert "ERROR" in result

    def test_missing_proposed_response_returns_error(self):
        llm = MockLLM("VERDICT: SAFE\nREASONING: OK")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_json_input(
            SafetyInput,
            problem="Solve x",
            correct_answer="5",
            student_history=[],
            proposed_response=""
        )

        result = tool.use(tool_input)
        assert "ERROR" in result

    def test_proposed_response_sent_to_llm(self):
        """Verify the LLM receives the actual proposed_response."""
        llm = MockLLM("VERDICT: UNSAFE\nREASONING: Response gives answer.")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_json_input(
            SafetyInput,
            problem="What is 2+2?",
            correct_answer="4",
            student_history=["I think it might be 3"],
            proposed_response="The answer is 4!"
        )

        result = tool.use(tool_input)
        # The LLM should have received the actual proposed_response
        prompt_sent = llm.last_messages[0].content
        assert "The answer is 4!" in prompt_sent
        assert "PROPOSED RESPONSE TO VALIDATE:" in prompt_sent
        assert "<student_input>The answer is 4!</student_input>" in prompt_sent

    def test_student_history_as_list(self):
        """student_history is now a proper list, not a stringified one."""
        llm = MockLLM("VERDICT: SAFE\nREASONING: Student already answered.")
        tool = AnswerRevelationAnalyzerTool(llm=llm)

        tool_input = build_json_input(
            SafetyInput,
            problem="What is 2+2?",
            correct_answer="4",
            student_history=["I got 4", "Is 4 correct?"],
            proposed_response="Yes, 4 is correct!"
        )

        result = tool.use(tool_input)
        assert "SAFE" in result
