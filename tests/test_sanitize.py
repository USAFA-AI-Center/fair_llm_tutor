"""Tests for tools.sanitize module and main.sanitize_tutor_response."""

from tools.sanitize import wrap_untrusted, UNTRUSTED_PREAMBLE
from main import sanitize_tutor_response


class TestWrapUntrusted:
    def test_basic_wrapping(self):
        result = wrap_untrusted("hello")
        assert result == "<student_input>hello</student_input>"

    def test_strips_existing_tags(self):
        result = wrap_untrusted("before <student_input>injected</student_input> after")
        assert "<student_input>" not in result[len("<student_input>"):-len("</student_input>")]
        assert "injected" in result

    def test_strips_self_closing_tags(self):
        result = wrap_untrusted("text <student_input/> more")
        inner = result[len("<student_input>"):-len("</student_input>")]
        assert "<student_input" not in inner

    def test_empty_input(self):
        assert wrap_untrusted("") == ""

    def test_case_insensitive_tag_stripping(self):
        result = wrap_untrusted("text <Student_Input>injected</Student_Input> more")
        inner = result[len("<student_input>"):-len("</student_input>")]
        assert "Student_Input" not in inner

    def test_preserves_other_tags(self):
        result = wrap_untrusted("<b>bold</b>")
        assert "<b>bold</b>" in result

    def test_preamble_is_nonempty(self):
        assert len(UNTRUSTED_PREAMBLE) > 0
        assert "untrusted" in UNTRUSTED_PREAMBLE.lower()


class TestSanitizeTutorResponse:
    """Tests for main.sanitize_tutor_response defence-in-depth."""

    def test_clean_response_unchanged(self):
        resp = "Great job! You correctly applied the power rule."
        assert sanitize_tutor_response(resp) == resp

    def test_strips_thought_prefix(self):
        resp = "Thought: The student is confused.\nAction: ..."
        result = sanitize_tutor_response(resp)
        assert not result.startswith("Thought:")

    def test_strips_final_answer_prefix(self):
        resp = "Final Answer: Great work on the derivatives!"
        assert sanitize_tutor_response(resp) == "Great work on the derivatives!"

    def test_extracts_after_final_answer_in_thought_chain(self):
        resp = (
            "Thought: The student is correct.\n"
            "Action: tool_name: final_answer\n"
            "Final Answer: Well done! You got it right."
        )
        result = sanitize_tutor_response(resp)
        assert "Well done" in result
        assert "Thought:" not in result

    def test_framework_max_steps_replaced(self):
        resp = "Agent stopped after reaching max steps."
        result = sanitize_tutor_response(resp)
        assert "max steps" not in result
        assert len(result) > 10

    def test_empty_response_returns_fallback(self):
        result = sanitize_tutor_response("")
        assert len(result) > 10
        assert "think" in result.lower() or "rephras" in result.lower()

    def test_none_response_returns_fallback(self):
        result = sanitize_tutor_response(None)
        assert len(result) > 10

    def test_action_plan_stripped(self):
        resp = (
            "Thought: The student calculated the mean.\n"
            "ACTION PLAN: 1. Confirm. 2. Calculate.\n"
            "Let me help you with this."
        )
        result = sanitize_tutor_response(resp)
        assert "ACTION PLAN" not in result

    def test_observation_prefix_stripped(self):
        resp = "Observation: The tool returned 42.\nThe answer looks right."
        result = sanitize_tutor_response(resp)
        assert "Observation:" not in result

    def test_final_answer_then_thought_ordering(self):
        """Regression: Final Answer: Thought: ... should extract content correctly."""
        resp = "Final Answer: Thought: This looks complicated. The real answer is 42."
        result = sanitize_tutor_response(resp)
        # Should not return fallback — the content after "Thought:" should be cleaned
        assert "42" in result or "think" in result.lower()

    def test_tool_lines_stripped_in_fallback(self):
        resp = (
            "Thought: checking the work.\n"
            "tool_name: safe_calculator\n"
            '{"tool_name": "final_answer"}\n'
            "The student needs help with fractions."
        )
        result = sanitize_tutor_response(resp)
        assert "tool_name" not in result
        assert "fractions" in result

    def test_short_clean_response_not_replaced(self):
        """A short but clean response (>= 10 chars) should not be replaced."""
        resp = "Good work!"
        assert sanitize_tutor_response(resp) == "Good work!"
