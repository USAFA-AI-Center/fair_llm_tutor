"""Stress tests from a real student's perspective.

These test realistic, messy student inputs against the mode detection
heuristic, SafetyGuard bypass path, field parsing edge cases, and hint
escalation. Each test documents the *expected student intent* so failures
surface as design gaps, not just code bugs.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.manager_agent import TutorManagerAgent
from tests.conftest import MockLLM, MockRetriever, build_tool_input


# ============================================================================
# 1. Mode detection — misclassified student inputs
# ============================================================================


class TestModeDetectionFalseHints:
    """Inputs that are clearly concept requests but contain HINT-trigger words."""

    def test_i_got_confused(self):
        """'I got confused' is a concept request, not work submission.
        'i got confused' cancels the HINT signal and flips to concept."""
        result = TutorManagerAgent.detect_mode("I got confused about how to do this")
        assert result == "CONCEPT_EXPLANATION"

    def test_i_got_stuck_on_derivatives(self):
        """'I got stuck on derivatives' — asking for help, not submitting work.
        'i got stuck' cancels the HINT signal and flips to concept."""
        result = TutorManagerAgent.detect_mode("I got stuck on derivatives")
        assert result == "CONCEPT_EXPLANATION"

    def test_i_got_no_idea_what_momentum_is(self):
        """'what is' (+1 concept), '?' (+1 concept) = 2 concept.
        'i got' (+1 hint) = 1 hint. Should correctly detect CONCEPT."""
        result = TutorManagerAgent.detect_mode(
            "I got no idea, what is momentum?"
        )
        assert result == "CONCEPT_EXPLANATION"

    def test_can_you_help_me_i_calculated_wrong(self):
        """Mixed signals: 'can you' (+1), 'help me' (+1) = 2 concept.
        'i calculated' (+1 hint) = 1 hint. Concept wins — correct."""
        result = TutorManagerAgent.detect_mode(
            "Can you help me? I calculated something wrong"
        )
        # '?' at end adds +1 concept → 3 concept vs 1 hint
        assert result == "CONCEPT_EXPLANATION"


class TestModeDetectionFalseConcepts:
    """Inputs that are clearly work submissions but contain CONCEPT-trigger words."""

    def test_explain_why_my_answer_is_wrong(self):
        """Student submitting work + asking for explanation.
        concept: 'explain' (+1), 'why' (+1) = 2.
        hint: 'x=7' has '=' + number (+1), and '7 is' matches number+alpha (+1) = 2.
        Tie with both > 0 → HINT (safer, runs SafetyGuard)."""
        result = TutorManagerAgent.detect_mode(
            "explain why my answer of x=7 is wrong"
        )
        assert result == "HINT"

    def test_help_me_check_50kg(self):
        """Student wants work checked.
        concept: 'help me' (+1) = 1.
        hint: '50kg' number+alpha (+1) = 1. Tie → HINT (safer)."""
        result = TutorManagerAgent.detect_mode(
            "help me check if 50kg*m/s is right"
        )
        assert result == "HINT"

    def test_what_is_5_times_10(self):
        """'what is 5 * 10?' — concept framing around arithmetic.
        concept: '?' (+1), 'what is' (+1) = 2.
        hint: '5 * 10' arithmetic (+1) = 1. Concept wins."""
        result = TutorManagerAgent.detect_mode("What is 5 * 10?")
        # Could go either way — in tutoring context this is arguably fine
        assert result == "CONCEPT_EXPLANATION"

    def test_why_is_my_answer_of_50_wrong(self):
        """concept: '?' (+1), 'why' (+1) = 2.
        hint: '50' + 'wrong' → '50 wrong' matches number+alpha (+1) = 1.
        Concept wins — but the student has submitted an answer (50)!"""
        result = TutorManagerAgent.detect_mode(
            "Why is my answer of 50 wrong?"
        )
        assert result == "CONCEPT_EXPLANATION", (
            "Concept wins, but this input contains a specific answer (50) — "
            "SafetyGuard bypass is risky here"
        )


class TestModeDetectionAmbiguous:
    """Truly ambiguous or unusual student inputs."""

    def test_just_a_number(self):
        """Student just types '42'. hint: no patterns except...
        '42' alone — number+alpha? No alpha after 42. No = sign.
        No arithmetic. hint=0, concept=0. → None."""
        result = TutorManagerAgent.detect_mode("42")
        assert result is None

    def test_emoji_and_frustration(self):
        """Real students express frustration. No patterns match."""
        result = TutorManagerAgent.detect_mode("ugh I don't get this at all")
        assert result is None

    def test_pasted_equation(self):
        r"""Student pastes 'f(x) = 3x^2 + 2x - 1'.
        hint: '= 3' equals+number (+1). '3x' number+alpha (+1).
        Arithmetic pattern \d+\s*[+-*/]\s*\d+ may match substrings.
        Regardless, hint > 0."""
        result = TutorManagerAgent.detect_mode("f(x) = 3x^2 + 2x - 1")
        assert result == "HINT"

    def test_multiline_student_work(self):
        """Student pastes multiple lines of work."""
        work = "Step 1: p = m * v\nStep 2: p = 5 * 10\nStep 3: p = 50 kg*m/s"
        result = TutorManagerAgent.detect_mode(work)
        assert result == "HINT"

    def test_very_long_concept_question(self):
        """Long but clearly conceptual."""
        q = (
            "I've been reading about thermodynamics and I'm confused about "
            "entropy. Can you explain what it means when they say entropy "
            "always increases? Why does that happen?"
        )
        result = TutorManagerAgent.detect_mode(q)
        assert result == "CONCEPT_EXPLANATION"


# ============================================================================
# 2. SafetyGuard bypass — concept mode with answer-revealing content
# ============================================================================


class TestSafetyBypassRisks:
    """Verify has_answer_content() catches answer-revealing concept questions.

    When detect_mode returns CONCEPT_EXPLANATION, the preprocessor checks
    has_answer_content(). If True, it adds a warning forcing SafetyGuard.
    """

    def test_concept_question_with_answer_in_it(self):
        """'Can you explain why 50 is the answer?' — CONCEPT mode wins,
        but has_answer_content detects '50 is' and forces SafetyGuard."""
        text = "Can you explain why 50 is the answer?"
        result = TutorManagerAgent.detect_mode(text)
        assert result == "CONCEPT_EXPLANATION"
        # But the safety net catches it
        assert TutorManagerAgent.has_answer_content(text) is True

    def test_concept_with_correct_calculation(self):
        """Student says 'what is p = mv? like if m=5 and v=10, p = 50?'
        This is concept-framed but contains the full worked answer."""
        text = "what is p = mv? like if m=5 and v=10, p = 50?"
        # Regardless of mode, has_answer_content must catch this
        assert TutorManagerAgent.has_answer_content(text) is True

    def test_confirm_my_understanding(self):
        """'So the answer to problem 3 is definitely 42, right?
        Can you explain why?' — has 'the answer' + digits."""
        text = "So the answer to problem 3 is definitely 42, right? Can you explain why?"
        result = TutorManagerAgent.detect_mode(text)
        assert result == "CONCEPT_EXPLANATION"
        assert TutorManagerAgent.has_answer_content(text) is True

    def test_pure_concept_no_false_alarm(self):
        """'What is momentum?' — no answer content, SafetyGuard skip is safe."""
        text = "What is momentum?"
        assert TutorManagerAgent.has_answer_content(text) is False

    def test_concept_with_chapter_number_no_false_alarm(self):
        """'What is the concept from chapter 5?' — digit present but
        no answer indicators (no units, no equals, no 'the answer')."""
        text = "What is the concept from chapter 5?"
        # "5?" — digit + "?" but "?" is not alpha, so number+alpha doesn't match.
        assert TutorManagerAgent.has_answer_content(text) is False


# ============================================================================
# 3. Field parsing edge cases — student content that breaks delimiters
# ============================================================================


class TestFieldParsingEdgeCases:
    """Student content that could break the ||| delimiter parsing."""

    def _make_diagnostic_tool(self):
        from tools.diagnostic_tools import StudentWorkAnalyzerTool
        return StudentWorkAnalyzerTool(llm=MockLLM(), retriever=MockRetriever())

    def _make_hint_tool(self):
        from tools.pedagogical_tools import SocraticHintGeneratorTool
        return SocraticHintGeneratorTool(llm=MockLLM("hint text"), retriever=MockRetriever())

    def test_student_work_contains_triple_pipe(self):
        """If the LLM embeds student work that itself contains '|||',
        the parser will split in the wrong place."""
        tool = self._make_diagnostic_tool()
        # Simulating what happens if student typed "a ||| b" and the manager
        # passes it through without escaping
        result = tool.use(
            "PROBLEM: Solve x ||| STUDENT_WORK: I tried a ||| b approach ||| TOPIC: algebra"
        )
        # The parser will see 4 parts instead of 3:
        # "PROBLEM: Solve x", "STUDENT_WORK: I tried a", "b approach", "TOPIC: algebra"
        # "b approach" won't match any field prefix, so it's silently dropped.
        # STUDENT_WORK becomes "I tried a" (truncated)
        # This still "works" but with corrupted student work.
        assert "ERROR" not in result  # No validation error — silent corruption

    def test_student_work_contains_field_prefix(self):
        """Student writes something like 'TOPIC: I think the topic is wrong'.
        If embedded in tool input, it could hijack field parsing."""
        tool = self._make_diagnostic_tool()
        result = tool.use(
            "PROBLEM: Explain TOPIC: gravity ||| STUDENT_WORK: I think so ||| TOPIC: physics"
        )
        # "PROBLEM: Explain TOPIC: gravity" — split(":", 1) gives "Explain TOPIC: gravity"
        # TOPIC field is parsed correctly from the last part.
        # The problem text includes "TOPIC: gravity" which is noise but not a crash.
        assert "ERROR" not in result

    def test_colon_in_student_answer(self):
        """Student's work contains colons (e.g., ratios like '2:3')."""
        tool = self._make_diagnostic_tool()
        result = tool.use(
            "PROBLEM: What is the ratio? ||| STUDENT_WORK: The ratio is 2:3 ||| TOPIC: math"
        )
        # split(":", 1) on "STUDENT_WORK: The ratio is 2:3" gives
        # "The ratio is 2:3" — correctly preserved.
        assert "ERROR" not in result

    def test_empty_student_work_after_colon(self):
        """LLM generates 'STUDENT_WORK: ' with nothing after the colon."""
        tool = self._make_diagnostic_tool()
        result = tool.use(
            "PROBLEM: Solve x ||| STUDENT_WORK: ||| TOPIC: algebra"
        )
        assert "ERROR" in result
        assert "STUDENT_WORK" in result


# ============================================================================
# 4. Hint escalation — edge cases in HINT_LEVEL parsing
# ============================================================================


class TestHintEscalationEdgeCases:
    """Edge cases in HINT_LEVEL parsing and application."""

    def _make_tool(self):
        from tools.pedagogical_tools import SocraticHintGeneratorTool
        return SocraticHintGeneratorTool(
            llm=MockLLM("Socratic hint text"), retriever=MockRetriever()
        )

    def test_hint_level_float(self):
        """HINT_LEVEL: 2.5 — int() will raise ValueError, should fall back."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Critical", TOPIC="algebra",
            HINT_LEVEL="2.5"
        ))
        # int("2.5") raises ValueError → hint_level_override = None → severity default
        assert "Level 2" in result  # Critical → Level 2

    def test_hint_level_negative(self):
        """HINT_LEVEL: -1 — should clamp to 1."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Minor", TOPIC="algebra",
            HINT_LEVEL="-1"
        ))
        assert "Level 1" in result

    def test_hint_level_with_spaces(self):
        """HINT_LEVEL:  3  (extra whitespace)."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Minor", TOPIC="algebra",
            HINT_LEVEL="  3  "
        ))
        # strip() then int() should handle this
        assert "Level 3" in result

    def test_hint_level_ignored_in_concept_mode(self):
        """HINT_LEVEL in CONCEPT_EXPLANATION mode — should be ignored entirely."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="CONCEPT_EXPLANATION", CONCEPT="momentum",
            QUESTION="What is momentum?", TOPIC="physics",
            HINT_LEVEL="4"
        ))
        # Should generate a concept explanation, not a level-4 hint
        assert "CONCEPT EXPLANATION" in result
        assert "Level 4" not in result

    def test_hint_level_empty_string(self):
        """HINT_LEVEL: (empty) — int("") raises ValueError, should fall back."""
        tool = self._make_tool()
        result = tool.use(
            "MODE: HINT ||| PROBLEM: Solve 2x=10 ||| STUDENT_WORK: x=3 ||| "
            "MISCONCEPTION: error ||| SEVERITY: Major ||| TOPIC: algebra ||| HINT_LEVEL:"
        )
        assert "Level 2" in result  # Major → Level 2


# ============================================================================
# 5. End-to-end preprocessor integration — does prepending help or hurt?
# ============================================================================


class TestPreprocessorIntegration:
    """Test that detect_mode + request prepending produces correct strings."""

    def test_hint_prepended_for_work_submission(self):
        """Verify the preprocessor prefix is correctly formed for HINT."""
        student_work = "I calculated p = 5 * 10 = 50 kg*m/s"
        detected = TutorManagerAgent.detect_mode(student_work)
        assert detected == "HINT"

        request = f"PROBLEM: Calculate momentum\n\nSTUDENT WORK: {student_work}"
        if detected:
            request = f"PREPROCESSOR DETECTED MODE: {detected}\n\n{request}"

        assert request.startswith("PREPROCESSOR DETECTED MODE: HINT")

    def test_concept_prepended_for_question(self):
        """Verify CONCEPT_EXPLANATION prefix for a question."""
        student_work = "What is the relationship between force and acceleration?"
        detected = TutorManagerAgent.detect_mode(student_work)
        assert detected == "CONCEPT_EXPLANATION"

        request = f"PROBLEM: General physics\n\nSTUDENT WORK: {student_work}"
        if detected:
            request = f"PREPROCESSOR DETECTED MODE: {detected}\n\n{request}"

        assert request.startswith("PREPROCESSOR DETECTED MODE: CONCEPT_EXPLANATION")

    def test_no_prefix_for_ambiguous_input(self):
        """Ambiguous input should not prepend any mode hint."""
        student_work = "hmm"
        detected = TutorManagerAgent.detect_mode(student_work)
        assert detected is None

        request = f"PROBLEM: Solve x\n\nSTUDENT WORK: {student_work}"
        if detected:
            request = f"PREPROCESSOR DETECTED MODE: {detected}\n\n{request}"

        assert not request.startswith("PREPROCESSOR DETECTED MODE:")

    def test_i_got_stuck_now_correctly_detected(self):
        """'I got stuck on derivatives' — preprocessor now correctly
        cancels the 'I got' HINT signal and detects CONCEPT_EXPLANATION."""
        student_work = "I got stuck on derivatives"
        detected = TutorManagerAgent.detect_mode(student_work)
        assert detected == "CONCEPT_EXPLANATION"

    def test_concept_with_answer_gets_safety_warning(self):
        """Concept question with embedded answer should produce a
        SafetyGuard warning in the preprocessor prefix."""
        student_work = "Can you explain why 50 kg*m/s is the answer?"
        detected = TutorManagerAgent.detect_mode(student_work)
        has_answer = TutorManagerAgent.has_answer_content(student_work)

        assert detected == "CONCEPT_EXPLANATION"
        assert has_answer is True

        # Simulate what main.py does
        request = f"PROBLEM: momentum\n\nSTUDENT WORK: {student_work}"
        if detected:
            prefix = f"PREPROCESSOR DETECTED MODE: {detected}"
            if detected == "CONCEPT_EXPLANATION" and has_answer:
                prefix += (
                    "\nPREPROCESSOR WARNING: Answer-like content detected. "
                    "SafetyGuard REQUIRED."
                )
            request = f"{prefix}\n\n{request}"

        assert "PREPROCESSOR WARNING" in request
        assert "SafetyGuard REQUIRED" in request
