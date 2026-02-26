"""Tests for tools/schemas.py — Pydantic I/O models."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.schemas import (
    InteractionMode,
    Severity,
    SafetyVerdict,
    DiagnosticInput,
    DiagnosticOutput,
    SafetyInput,
    SafetyOutput,
    HintInput,
    HintOutput,
)


class TestEnums:
    def test_interaction_mode_values(self):
        assert InteractionMode.HINT == "HINT"
        assert InteractionMode.CONCEPT_EXPLANATION == "CONCEPT_EXPLANATION"

    def test_severity_values(self):
        assert Severity.CRITICAL == "Critical"
        assert Severity.MAJOR == "Major"
        assert Severity.MINOR == "Minor"

    def test_safety_verdict_values(self):
        assert SafetyVerdict.SAFE == "SAFE"
        assert SafetyVerdict.UNSAFE == "UNSAFE"


class TestDiagnosticInput:
    def test_valid_input(self):
        d = DiagnosticInput(problem="Solve x+1=2", student_work="x=1", topic="algebra")
        assert d.problem == "Solve x+1=2"

    def test_roundtrip_json(self):
        d = DiagnosticInput(problem="Solve x+1=2", student_work="x=1", topic="algebra")
        json_str = d.model_dump_json()
        d2 = DiagnosticInput.model_validate_json(json_str)
        assert d == d2

    def test_missing_required_field_raises(self):
        with pytest.raises(Exception):
            DiagnosticInput(problem="Solve x")  # missing student_work, topic


class TestDiagnosticOutput:
    def test_valid_output(self):
        d = DiagnosticOutput(
            correct_aspects="Good approach",
            error_identified="Sign error",
            root_misconception="Subtraction confusion",
            severity=Severity.MINOR,
            suggested_focus="Arithmetic",
            evidence="Student wrote -3 instead of +3",
        )
        assert d.severity == Severity.MINOR

    def test_roundtrip_json(self):
        d = DiagnosticOutput(
            correct_aspects="Good",
            error_identified="None",
            root_misconception="None",
            severity=Severity.MINOR,
            suggested_focus="Continue",
            evidence="All correct",
        )
        json_str = d.model_dump_json()
        d2 = DiagnosticOutput.model_validate_json(json_str)
        assert d == d2


class TestSafetyInput:
    def test_valid_input(self):
        s = SafetyInput(
            problem="Solve x",
            correct_answer="5",
            student_history=[],
            proposed_response="Think about it.",
        )
        assert s.proposed_response == "Think about it."

    def test_roundtrip_json(self):
        s = SafetyInput(
            problem="Solve x",
            correct_answer="5",
            student_history=["I got 3"],
            proposed_response="Check again.",
        )
        json_str = s.model_dump_json()
        s2 = SafetyInput.model_validate_json(json_str)
        assert s == s2


class TestSafetyOutput:
    def test_valid_output(self):
        s = SafetyOutput(
            verdict=SafetyVerdict.SAFE,
            reasoning="No answer revealed",
            student_already_answered=False,
            confidence="High",
        )
        assert s.verdict == SafetyVerdict.SAFE


class TestHintInput:
    def test_hint_mode(self):
        h = HintInput(
            mode=InteractionMode.HINT,
            problem="Solve 2x=10",
            student_work="x=3",
            misconception="Division error",
            severity=Severity.MINOR,
            topic="algebra",
        )
        assert h.mode == InteractionMode.HINT

    def test_concept_mode(self):
        h = HintInput(
            mode=InteractionMode.CONCEPT_EXPLANATION,
            topic="physics",
            concept="momentum",
            question="What is momentum?",
        )
        assert h.concept == "momentum"

    def test_roundtrip_json(self):
        h = HintInput(
            mode=InteractionMode.HINT,
            problem="Solve 2x=10",
            student_work="x=3",
            misconception="Division error",
            severity=Severity.MINOR,
            topic="algebra",
        )
        json_str = h.model_dump_json()
        h2 = HintInput.model_validate_json(json_str)
        assert h == h2


class TestHintOutput:
    def test_valid_output(self):
        h = HintOutput(
            hint_text="Check your division",
            hint_level=3,
            mode=InteractionMode.HINT,
        )
        assert h.hint_level == 3
