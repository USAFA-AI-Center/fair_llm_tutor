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
from tests.conftest import MockLLM, MockRetriever, build_tool_input, build_json_input
from tools.schemas import DiagnosticInput, HintInput, InteractionMode, Severity


# ============================================================================
# 1. Mode detection — misclassified student inputs
# ============================================================================


class TestNonSTEMModeDetection:
    """Mode detection for non-STEM domains (literature, history, code)."""

    def test_literature_essay_with_question(self):
        """Student asks about their essay — concept question, not work submission."""
        result = TutorManagerAgent.detect_mode(
            "Can you explain what makes a good thesis statement?"
        )
        assert result == "CONCEPT_EXPLANATION"

    def test_code_output_with_numbers(self):
        """Student shares code output — numbers trigger HINT correctly."""
        result = TutorManagerAgent.detect_mode(
            "I got output = 15 but the expected output is 20"
        )
        assert result == "HINT"

    def test_history_date_submission(self):
        """Student submits a historical date — numbers trigger HINT."""
        result = TutorManagerAgent.detect_mode(
            "I think the French Revolution started in 1788"
        )
        assert result == "HINT"

    def test_music_theory_question(self):
        """Pure concept question about music theory."""
        result = TutorManagerAgent.detect_mode(
            "What is the difference between major and minor scales?"
        )
        assert result == "CONCEPT_EXPLANATION"

    def test_programming_debug_submission(self):
        """Student submitting debug output with values."""
        result = TutorManagerAgent.detect_mode(
            "My function returned [1, 2, 3] instead of [3, 2, 1]"
        )
        assert result == "HINT"


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
    """Edge cases in JSON input parsing for diagnostic tool."""

    def _make_diagnostic_tool(self):
        from tools.diagnostic_tools import StudentWorkAnalyzerTool
        return StudentWorkAnalyzerTool(llm=MockLLM(), retriever=MockRetriever())

    def _make_hint_tool(self):
        from tools.pedagogical_tools import SocraticHintGeneratorTool
        return SocraticHintGeneratorTool(llm=MockLLM("hint text"), retriever=MockRetriever())

    def test_student_work_with_special_chars_in_json(self):
        """JSON correctly handles special characters that broke ||| parsing."""
        tool = self._make_diagnostic_tool()
        tool_input = build_json_input(
            DiagnosticInput,
            problem="Solve x",
            student_work='I tried a ||| b approach',
            topic="algebra"
        )
        result = tool.use(tool_input)
        # JSON preserves the full student work — no silent corruption
        assert "ERROR" not in result

    def test_student_work_with_field_prefix_in_json(self):
        """JSON handles student work containing 'TOPIC:' without hijacking."""
        tool = self._make_diagnostic_tool()
        tool_input = build_json_input(
            DiagnosticInput,
            problem="Explain TOPIC: gravity",
            student_work="I think so",
            topic="physics"
        )
        result = tool.use(tool_input)
        assert "ERROR" not in result

    def test_student_work_with_colons_in_json(self):
        """JSON handles colons in student work (e.g., ratios '2:3')."""
        tool = self._make_diagnostic_tool()
        tool_input = build_json_input(
            DiagnosticInput,
            problem="What is the ratio?",
            student_work="The ratio is 2:3",
            topic="math"
        )
        result = tool.use(tool_input)
        assert "ERROR" not in result

    def test_empty_student_work_in_json(self):
        """Empty student_work field returns validation error."""
        tool = self._make_diagnostic_tool()
        tool_input = build_json_input(
            DiagnosticInput,
            problem="Solve x",
            student_work="",
            topic="algebra"
        )
        result = tool.use(tool_input)
        assert "ERROR" in result
        assert "student_work" in result.lower()


# ============================================================================
# 4. Hint escalation — edge cases in HINT_LEVEL parsing
# ============================================================================


class TestHintEscalationEdgeCases:
    """Edge cases in hint_level handling with JSON input."""

    def _make_tool(self):
        from tools.pedagogical_tools import SocraticHintGeneratorTool
        return SocraticHintGeneratorTool(
            llm=MockLLM("Socratic hint text"), retriever=MockRetriever()
        )

    def test_hint_level_negative(self):
        """hint_level=-1 should clamp to 1."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="division error", severity=Severity.MINOR, topic="algebra",
            hint_level=-1
        ))
        assert "Level 1" in result

    def test_hint_level_ignored_in_concept_mode(self):
        """hint_level in CONCEPT_EXPLANATION mode should be ignored entirely."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.CONCEPT_EXPLANATION, concept="momentum",
            question="What is momentum?", topic="physics",
            hint_level=4
        ))
        assert "CONCEPT EXPLANATION" in result
        assert "Level 4" not in result

    def test_hint_level_none_uses_severity_default(self):
        """Without hint_level, severity determines level as before."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="error", severity=Severity.MAJOR, topic="algebra"
        ))
        assert "Level 2" in result  # Major → Level 2

    def test_hint_level_large_value_clamped(self):
        """hint_level=100 should clamp to Level 4."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="error", severity=Severity.MINOR, topic="algebra",
            hint_level=100
        ))
        assert "Level 4" in result


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
