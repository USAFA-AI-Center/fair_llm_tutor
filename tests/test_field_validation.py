"""Tests for field validation in tool use() methods."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM, MockRetriever, build_json_input
from tools.schemas import DiagnosticInput, SafetyInput, HintInput, InteractionMode, Severity


class TestDiagnosticToolValidation:
    """Field validation for StudentWorkAnalyzerTool (JSON input)."""

    def _make_tool(self):
        from tools.diagnostic_tools import StudentWorkAnalyzerTool
        return StudentWorkAnalyzerTool(llm=MockLLM(), retriever=MockRetriever())

    def test_missing_problem(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            DiagnosticInput, problem="", student_work="x=5", topic="algebra"
        ))
        assert "ERROR" in result
        assert "problem" in result.lower()

    def test_missing_student_work(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            DiagnosticInput, problem="Solve x+1=2", student_work="", topic="algebra"
        ))
        assert "ERROR" in result
        assert "student_work" in result.lower()

    def test_missing_topic(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            DiagnosticInput, problem="Solve x+1=2", student_work="x=1", topic=""
        ))
        assert "ERROR" in result
        assert "topic" in result.lower()

    def test_valid_input_succeeds(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            DiagnosticInput, problem="Solve x+1=2", student_work="x=1", topic="algebra"
        ))
        assert "ERROR: Missing" not in result

    def test_invalid_json_returns_error(self):
        tool = self._make_tool()
        result = tool.use("not json at all")
        assert "ERROR" in result


class TestPedagogicalToolValidation:
    """Field validation for SocraticHintGeneratorTool (JSON input)."""

    def _make_tool(self):
        from tools.pedagogical_tools import SocraticHintGeneratorTool
        return SocraticHintGeneratorTool(llm=MockLLM(), retriever=MockRetriever())

    def test_concept_mode_missing_concept(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.CONCEPT_EXPLANATION,
            concept="",
            question="What is it?",
            topic="physics"
        ))
        assert "ERROR" in result
        assert "concept" in result.lower()

    def test_concept_mode_valid(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.CONCEPT_EXPLANATION,
            concept="momentum",
            question="What is momentum?",
            topic="physics"
        ))
        assert "ERROR: Missing" not in result

    def test_hint_mode_missing_problem(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="",
            student_work="x=5",
            misconception="error",
            severity=Severity.MINOR,
            topic="algebra"
        ))
        assert "ERROR" in result
        assert "problem" in result.lower()

    def test_hint_mode_valid(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Solve x+1=2",
            student_work="x=5",
            misconception="wrong",
            severity=Severity.MINOR,
            topic="algebra"
        ))
        assert "ERROR: Missing" not in result

    def test_invalid_json_returns_error(self):
        tool = self._make_tool()
        result = tool.use("not json")
        assert "ERROR" in result


class TestSafetyToolValidation:
    """Field validation for AnswerRevelationAnalyzerTool (JSON input)."""

    def _make_tool(self):
        from tools.safety_tools import AnswerRevelationAnalyzerTool
        return AnswerRevelationAnalyzerTool(llm=MockLLM(
            "VERDICT: SAFE\nREASONING: OK\nSTUDENT_ALREADY_ANSWERED: NO\nCONFIDENCE: High"
        ))

    def test_missing_proposed_response(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            SafetyInput,
            problem="Solve x",
            correct_answer="5",
            student_history=[],
            proposed_response=""
        ))
        assert "ERROR" in result
        assert "proposed_response" in result.lower()

    def test_valid_input_succeeds(self):
        tool = self._make_tool()
        result = tool.use(build_json_input(
            SafetyInput,
            problem="Solve x",
            correct_answer="5",
            student_history=[],
            proposed_response="Think about what x equals"
        ))
        assert "ERROR: Missing" not in result

    def test_invalid_json_returns_error(self):
        tool = self._make_tool()
        result = tool.use("not json")
        assert "ERROR" in result
