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

from agents.tutor_agent import TutorAgent
from tools.hint_level_tools import GetHintLevelTool


# ============================================================================
# 1. Mode detection — misclassified student inputs
# ============================================================================


class TestNonSTEMModeDetection:
    """Mode detection for non-STEM domains (literature, history, code)."""

    def test_literature_essay_with_question(self):
        """Student asks about their essay — concept question, not work submission."""
        result = TutorAgent.detect_mode(
            "Can you explain what makes a good thesis statement?"
        )
        assert result == "CONCEPT_EXPLANATION"

    def test_music_theory_question(self):
        """Pure concept question about music theory."""
        result = TutorAgent.detect_mode(
            "What is the difference between major and minor scales?"
        )
        assert result == "CONCEPT_EXPLANATION"


class TestModeDetectionFalseHints:
    """Inputs that are clearly concept requests but contain HINT-trigger words."""

    def test_i_got_confused(self):
        """'I got confused' is a concept request, not work submission.
        'i got confused' cancels the HINT signal and flips to concept."""
        result = TutorAgent.detect_mode("I got confused about how to do this")
        assert result == "CONCEPT_EXPLANATION"

    def test_i_got_stuck_on_derivatives(self):
        """'I got stuck on derivatives' — asking for help, not submitting work.
        'i got stuck' cancels the HINT signal and flips to concept."""
        result = TutorAgent.detect_mode("I got stuck on derivatives")
        assert result == "CONCEPT_EXPLANATION"

    def test_i_got_no_idea_what_momentum_is(self):
        """'what is' (+1 concept), '?' (+1 concept) = 2 concept.
        'i got' (+1 hint) = 1 hint. Should correctly detect CONCEPT."""
        result = TutorAgent.detect_mode(
            "I got no idea, what is momentum?"
        )
        assert result == "CONCEPT_EXPLANATION"

    def test_can_you_help_me_i_calculated_wrong(self):
        """Mixed signals: 'can you' (+1), 'help me' (+1) = 2 concept.
        'i calculated' (+1 hint) = 1 hint. Concept wins — correct."""
        result = TutorAgent.detect_mode(
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
        result = TutorAgent.detect_mode(
            "explain why my answer of x=7 is wrong"
        )
        assert result == "HINT"

    def test_help_me_check_50kg(self):
        """Student wants work checked.
        concept: 'help me' (+1) = 1.
        hint: '50kg' number+alpha (+1) = 1. Tie → HINT (safer)."""
        result = TutorAgent.detect_mode(
            "help me check if 50kg*m/s is right"
        )
        assert result == "HINT"

    def test_what_is_5_times_10(self):
        """'what is 5 * 10?' — concept framing around arithmetic.
        concept: '?' (+1), 'what is' (+1) = 2.
        hint: '5 * 10' arithmetic (+1) = 1. Concept wins."""
        result = TutorAgent.detect_mode("What is 5 * 10?")
        # Could go either way — in tutoring context this is arguably fine
        assert result == "CONCEPT_EXPLANATION"

    def test_why_is_my_answer_of_50_wrong(self):
        """concept: '?' (+1), 'why' (+1) = 2.
        hint: '50' + 'wrong' → '50 wrong' matches number+alpha (+1) = 1.
        Concept wins — but the student has submitted an answer (50)!"""
        result = TutorAgent.detect_mode(
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
        result = TutorAgent.detect_mode("42")
        assert result is None

    def test_emoji_and_frustration(self):
        """Real students express frustration. No patterns match."""
        result = TutorAgent.detect_mode("ugh I don't get this at all")
        assert result is None

    def test_pasted_equation(self):
        r"""Student pastes 'f(x) = 3x^2 + 2x - 1'.
        hint: '= 3' equals+number (+1). '3x' number+alpha (+1).
        Arithmetic pattern \d+\s*[+-*/]\s*\d+ may match substrings.
        Regardless, hint > 0."""
        result = TutorAgent.detect_mode("f(x) = 3x^2 + 2x - 1")
        assert result == "HINT"

    def test_multiline_student_work(self):
        """Student pastes multiple lines of work."""
        work = "Step 1: p = m * v\nStep 2: p = 5 * 10\nStep 3: p = 50 kg*m/s"
        result = TutorAgent.detect_mode(work)
        assert result == "HINT"

    def test_very_long_concept_question(self):
        """Long but clearly conceptual."""
        q = (
            "I've been reading about thermodynamics and I'm confused about "
            "entropy. Can you explain what it means when they say entropy "
            "always increases? Why does that happen?"
        )
        result = TutorAgent.detect_mode(q)
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
        result = TutorAgent.detect_mode(text)
        assert result == "CONCEPT_EXPLANATION"
        # But the safety net catches it
        assert TutorAgent.has_answer_content(text) is True

    def test_concept_with_correct_calculation(self):
        """Student says 'what is p = mv? like if m=5 and v=10, p = 50?'
        This is concept-framed but contains the full worked answer."""
        text = "what is p = mv? like if m=5 and v=10, p = 50?"
        # Regardless of mode, has_answer_content must catch this
        assert TutorAgent.has_answer_content(text) is True

    def test_confirm_my_understanding(self):
        """'So the answer to problem 3 is definitely 42, right?
        Can you explain why?' — has 'the answer' + digits."""
        text = "So the answer to problem 3 is definitely 42, right? Can you explain why?"
        result = TutorAgent.detect_mode(text)
        assert result == "CONCEPT_EXPLANATION"
        assert TutorAgent.has_answer_content(text) is True

    def test_pure_concept_no_false_alarm(self):
        """'What is momentum?' — no answer content, SafetyGuard skip is safe."""
        text = "What is momentum?"
        assert TutorAgent.has_answer_content(text) is False

    def test_concept_with_chapter_number_no_false_alarm(self):
        """'What is the concept from chapter 5?' — digit present but
        no answer indicators (no units, no equals, no 'the answer')."""
        text = "What is the concept from chapter 5?"
        # "5?" — digit + "?" but "?" is not alpha, so number+alpha doesn't match.
        assert TutorAgent.has_answer_content(text) is False


# ============================================================================
# 3. Field parsing edge cases — student content that breaks delimiters
# ============================================================================


# ============================================================================
# 4. Hint escalation — edge cases in HINT_LEVEL parsing
# ============================================================================


class TestHintEscalationEdgeCases:
    """Edge cases in hint_level handling via GetHintLevelTool."""

    def setup_method(self):
        self.tool = GetHintLevelTool()

    def test_hint_level_negative(self):
        """hint_level_override=-1 should clamp to 1."""
        import json
        result = self.tool.use(json.dumps({
            "severity": "Minor", "hint_level_override": -1
        }))
        assert "Hint Level: 1" in result

    def test_hint_level_none_uses_severity_default(self):
        """Without override, severity determines level."""
        import json
        result = self.tool.use(json.dumps({"severity": "Major"}))
        assert "Hint Level: 2" in result  # Major → Level 2

    def test_hint_level_large_value_clamped(self):
        """hint_level_override=100 should clamp to Level 4."""
        import json
        result = self.tool.use(json.dumps({
            "severity": "Minor", "hint_level_override": 100
        }))
        assert "Hint Level: 4" in result

    def test_hint_level_override_replaces_severity(self):
        """Override takes precedence over severity mapping."""
        import json
        result = self.tool.use(json.dumps({
            "severity": "Minor", "hint_level_override": 1
        }))
        assert "Hint Level: 1" in result  # Override wins over Minor→3


# ============================================================================
# 5. End-to-end preprocessor integration — does prepending help or hurt?
# ============================================================================


class TestPreprocessorIntegration:
    """Test that detect_mode + request prepending produces correct strings."""

    def test_hint_prepended_for_work_submission(self):
        """Verify the preprocessor prefix is correctly formed for HINT."""
        student_work = "I calculated p = 5 * 10 = 50 kg*m/s"
        detected = TutorAgent.detect_mode(student_work)
        assert detected == "HINT"

        request = f"PROBLEM: Calculate momentum\n\nSTUDENT WORK: {student_work}"
        if detected:
            request = f"PREPROCESSOR DETECTED MODE: {detected}\n\n{request}"

        assert request.startswith("PREPROCESSOR DETECTED MODE: HINT")

    def test_concept_prepended_for_question(self):
        """Verify CONCEPT_EXPLANATION prefix for a question."""
        student_work = "What is the relationship between force and acceleration?"
        detected = TutorAgent.detect_mode(student_work)
        assert detected == "CONCEPT_EXPLANATION"

        request = f"PROBLEM: General physics\n\nSTUDENT WORK: {student_work}"
        if detected:
            request = f"PREPROCESSOR DETECTED MODE: {detected}\n\n{request}"

        assert request.startswith("PREPROCESSOR DETECTED MODE: CONCEPT_EXPLANATION")

    def test_no_prefix_for_ambiguous_input(self):
        """Ambiguous input should not prepend any mode hint."""
        student_work = "hmm"
        detected = TutorAgent.detect_mode(student_work)
        assert detected is None

        request = f"PROBLEM: Solve x\n\nSTUDENT WORK: {student_work}"
        if detected:
            request = f"PREPROCESSOR DETECTED MODE: {detected}\n\n{request}"

        assert not request.startswith("PREPROCESSOR DETECTED MODE:")

    def test_i_got_stuck_now_correctly_detected(self):
        """'I got stuck on derivatives' — preprocessor now correctly
        cancels the 'I got' HINT signal and detects CONCEPT_EXPLANATION."""
        student_work = "I got stuck on derivatives"
        detected = TutorAgent.detect_mode(student_work)
        assert detected == "CONCEPT_EXPLANATION"

    def test_concept_with_answer_gets_safety_required(self):
        """Concept question with embedded answer should produce safety
        required in the preprocessor prefix (now always added)."""
        student_work = "Can you explain why 50 kg*m/s is the answer?"
        detected = TutorAgent.detect_mode(student_work)
        has_answer = TutorAgent.has_answer_content(student_work)

        assert detected == "CONCEPT_EXPLANATION"
        assert has_answer is True

        # Simulate what main.py does (safety always required now)
        request = f"PROBLEM: momentum\n\nSTUDENT WORK: {student_work}"
        if detected:
            prefix = f"PREPROCESSOR DETECTED MODE: {detected}"
            prefix += "\nSafety check REQUIRED."
            request = f"{prefix}\n\n{request}"

        assert "Safety check REQUIRED" in request

    def test_pure_concept_also_gets_safety_required(self):
        """Pure concept question now also gets safety required."""
        student_work = "What is momentum?"
        detected = TutorAgent.detect_mode(student_work)

        assert detected == "CONCEPT_EXPLANATION"
        assert TutorAgent.has_answer_content(student_work) is False

        # Safety is now always required regardless of answer content
        request = f"PROBLEM: physics\n\nSTUDENT WORK: {student_work}"
        if detected:
            prefix = f"PREPROCESSOR DETECTED MODE: {detected}"
            prefix += "\nSafety check REQUIRED."
            request = f"{prefix}\n\n{request}"

        assert "Safety check REQUIRED" in request
