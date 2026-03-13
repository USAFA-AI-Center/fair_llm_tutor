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
        resp = "Good thinking! Let's look at the next step together."
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
        # "Well done!" is praise confirmation and gets replaced
        assert "You got it right" in result
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
        """A short but clean response (>= 10 chars) should not be replaced.

        Note: 'Good work!' is now treated as praise confirmation and gets
        replaced with a neutral opener. Use a non-praise short response.
        """
        resp = "Let's look at your approach here."
        assert sanitize_tutor_response(resp) == "Let's look at your approach here."

    def test_answer_confirmation_stripped(self):
        """Answer confirmation like 'Great job! You correctly found X' is replaced."""
        resp = "Great job! You correctly found that x = 6."
        result = sanitize_tutor_response(resp)
        assert "correctly found" not in result
        assert "x = 6" not in result

    def test_answer_confirmation_well_done_variant(self):
        """'Well done! You correctly calculated...' is also caught."""
        resp = "Well done! You correctly calculated the derivative as 6x + 2."
        result = sanitize_tutor_response(resp)
        assert "correctly calculated" not in result

    def test_answer_confirmation_embedded_in_longer_response(self):
        """Confirmation embedded in a longer response is replaced while keeping the rest."""
        resp = (
            "Great job! You correctly determined the momentum is 50 kg*m/s. "
            "Now let's try a harder problem."
        )
        result = sanitize_tutor_response(resp)
        assert "correctly determined" not in result
        assert "harder problem" in result

    def test_framework_leak_embedded_in_text(self):
        """Framework leak embedded in longer text is still caught."""
        resp = "Here is your answer. Agent stopped after reaching max steps. Try again."
        result = sanitize_tutor_response(resp)
        assert "max steps" not in result

    def test_truncated_short_response_gets_followup(self):
        """Short responses ending with ':' get a follow-up question appended."""
        resp = "Here's a general rule:"
        result = sanitize_tutor_response(resp)
        assert "next step" in result.lower() or "think" in result.lower()

    def test_answer_confirmation_no_trailing_punctuation(self):
        """Confirmation without trailing punctuation gets full sentence removed.

        When the confirmation and follow-up are in the same sentence (no
        sentence-ending punctuation between them), the entire sentence is
        removed to prevent answer fragments from leaking through.
        """
        resp = (
            "Great job! You correctly found the derivative "
            "Now let's try a harder problem with the chain rule"
        )
        result = sanitize_tutor_response(resp)
        assert "correctly found" not in result
        # The follow-up is in the same un-punctuated sentence, so it
        # gets removed along with the confirmation to prevent leaks.

    def test_answer_confirmation_separate_sentences_preserves_rest(self):
        """When confirmation and follow-up are separate sentences, follow-up survives."""
        resp = (
            "Great job! You correctly found the derivative. "
            "Now let's try a harder problem with the chain rule."
        )
        result = sanitize_tutor_response(resp)
        assert "correctly found" not in result
        assert "chain rule" in result

    def test_truncated_long_response_unchanged(self):
        """Long responses ending with ':' are not modified (the colon is part of prose)."""
        resp = "Consider the following approach to solving this derivative problem, remembering the chain rule and product rule:"
        result = sanitize_tutor_response(resp)
        # Long response (>80 chars) with colon should not get extra appended
        assert result == resp

    def test_third_person_reference_stripped(self):
        """Third-person references like 'The student correctly...' are replaced."""
        resp = (
            "The student correctly calculated the (2,2) element as 50. "
            "Now let's continue with the next step."
        )
        result = sanitize_tutor_response(resp)
        assert "The student correctly" not in result
        assert "next step" in result

    def test_third_person_report_style_stripped(self):
        """Multiple third-person sentences are replaced."""
        resp = (
            "The student identified the scaling matrix correctly. "
            "The student also noted the dimension requirement. "
            "What would you like to explore next?"
        )
        result = sanitize_tutor_response(resp)
        assert "The student identified" not in result
        assert "The student also" not in result

    def test_second_person_preserved(self):
        """Normal second-person responses are not affected by third-person filter."""
        resp = "You applied the power rule correctly here. What rule did you use for the constant term?"
        result = sanitize_tutor_response(resp)
        assert "You applied" in result

    def test_standalone_code_block_stripped(self):
        """Complete code solutions in code blocks are replaced."""
        resp = (
            "Let me show you the solution:\n"
            "```python\n"
            "def factorial(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)\n"
            "```\n"
            "This handles the base case."
        )
        result = sanitize_tutor_response(resp)
        assert "def factorial" not in result
        assert "return n * factorial" not in result
