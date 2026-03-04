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
    RetrievalInput,
    HistoryCheckInput,
    HintLevelInput,
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


class TestRetrievalInput:
    def test_valid_input(self):
        r = RetrievalInput(query="momentum physics")
        assert r.query == "momentum physics"
        assert r.top_k == 3  # default

    def test_custom_top_k(self):
        r = RetrievalInput(query="test", top_k=5)
        assert r.top_k == 5

    def test_roundtrip_json(self):
        r = RetrievalInput(query="algebra errors", top_k=2)
        json_str = r.model_dump_json()
        r2 = RetrievalInput.model_validate_json(json_str)
        assert r == r2

    def test_missing_query_raises(self):
        with pytest.raises(Exception):
            RetrievalInput()  # query is required


class TestHistoryCheckInput:
    def test_valid_input(self):
        h = HistoryCheckInput(correct_answer="x = 6", student_history=["I got x = 7"])
        assert h.correct_answer == "x = 6"
        assert len(h.student_history) == 1

    def test_default_empty_history(self):
        h = HistoryCheckInput(correct_answer="42")
        assert h.student_history == []

    def test_roundtrip_json(self):
        h = HistoryCheckInput(correct_answer="42", student_history=["I got 42"])
        json_str = h.model_dump_json()
        h2 = HistoryCheckInput.model_validate_json(json_str)
        assert h == h2


class TestHintLevelInput:
    def test_valid_input(self):
        h = HintLevelInput(severity="Minor", hint_level_override=3)
        assert h.severity == "Minor"
        assert h.hint_level_override == 3

    def test_defaults(self):
        h = HintLevelInput()
        assert h.severity == "Major"
        assert h.hint_level_override is None

    def test_roundtrip_json(self):
        h = HintLevelInput(severity="Critical", hint_level_override=1)
        json_str = h.model_dump_json()
        h2 = HintLevelInput.model_validate_json(json_str)
        assert h == h2
