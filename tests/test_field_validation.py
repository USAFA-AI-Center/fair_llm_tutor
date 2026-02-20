"""Tests for field validation in tool use() methods."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM, MockRetriever, build_tool_input


class TestDiagnosticToolValidation:
    """Field validation for StudentWorkAnalyzerTool."""

    def _make_tool(self):
        from tools.diagnostic_tools import StudentWorkAnalyzerTool
        return StudentWorkAnalyzerTool(llm=MockLLM(), retriever=MockRetriever())

    def test_missing_problem(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(PROBLEM="", STUDENT_WORK="x=5", TOPIC="algebra"))
        assert "ERROR" in result
        assert "PROBLEM" in result

    def test_missing_student_work(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(PROBLEM="Solve x+1=2", STUDENT_WORK="", TOPIC="algebra"))
        assert "ERROR" in result
        assert "STUDENT_WORK" in result

    def test_missing_topic(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(PROBLEM="Solve x+1=2", STUDENT_WORK="x=1", TOPIC=""))
        assert "ERROR" in result
        assert "TOPIC" in result

    def test_valid_input_succeeds(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(PROBLEM="Solve x+1=2", STUDENT_WORK="x=1", TOPIC="algebra"))
        assert "ERROR: Missing" not in result


class TestPedagogicalToolValidation:
    """Field validation for SocraticHintGeneratorTool."""

    def _make_tool(self):
        from tools.pedagogical_tools import SocraticHintGeneratorTool
        return SocraticHintGeneratorTool(llm=MockLLM(), retriever=MockRetriever())

    def test_concept_mode_missing_concept(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(MODE="CONCEPT_EXPLANATION", CONCEPT="", QUESTION="What is it?", TOPIC="physics"))
        assert "ERROR" in result
        assert "CONCEPT" in result

    def test_concept_mode_valid(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(MODE="CONCEPT_EXPLANATION", CONCEPT="momentum", QUESTION="What is momentum?", TOPIC="physics"))
        assert "ERROR: Missing" not in result

    def test_hint_mode_missing_problem(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(MODE="HINT", PROBLEM="", STUDENT_WORK="x=5", MISCONCEPTION="error", SEVERITY="Minor", TOPIC="algebra"))
        assert "ERROR" in result
        assert "PROBLEM" in result

    def test_hint_mode_valid(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(MODE="HINT", PROBLEM="Solve x+1=2", STUDENT_WORK="x=5", MISCONCEPTION="wrong", SEVERITY="Minor", TOPIC="algebra"))
        assert "ERROR: Missing" not in result


class TestSafetyToolValidation:
    """Field validation for AnswerRevelationAnalyzerTool."""

    def _make_tool(self):
        from tools.safety_tools import AnswerRevelationAnalyzerTool
        return AnswerRevelationAnalyzerTool(llm=MockLLM(
            "VERDICT: SAFE\nREASONING: OK\nSTUDENT_ALREADY_ANSWERED: NO\nCONFIDENCE: High"
        ))

    def test_missing_proposed_response(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(PROBLEM="Solve x", CORRECT_ANSWER="5", STUDENT_HISTORY="[]", PROPOSED_RESPONSE=""))
        assert "ERROR" in result
        assert "PROPOSED_RESPONSE" in result

    def test_valid_input_succeeds(self):
        tool = self._make_tool()
        result = tool.use(build_tool_input(PROBLEM="Solve x", CORRECT_ANSWER="5", STUDENT_HISTORY="[]", PROPOSED_RESPONSE="Think about what x equals"))
        assert "ERROR: Missing" not in result
