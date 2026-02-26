"""Tests for diagnostic_tools.py — StudentWorkAnalyzerTool."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.diagnostic_tools import StudentWorkAnalyzerTool
from tools.schemas import DiagnosticInput
from tests.conftest import MockLLM, MockRetriever, build_json_input


class TestExtractSeverity:
    """Tests for _extract_severity."""

    def setup_method(self):
        self.tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )

    def test_critical_severity(self):
        response = "SEVERITY: Critical\nThe student fundamentally misunderstands."
        assert self.tool._extract_severity(response) == "Critical"

    def test_major_severity(self):
        response = "SEVERITY: Major\nSignificant error in approach."
        assert self.tool._extract_severity(response) == "Major"

    def test_minor_severity(self):
        response = "SEVERITY: Minor\nSmall computational error."
        assert self.tool._extract_severity(response) == "Minor"

    def test_fallback_to_major(self):
        response = "The student made an error but I can't classify it."
        assert self.tool._extract_severity(response) == "Major"

    def test_fallback_critical_in_body(self):
        response = "This is a CRITICAL misunderstanding of the concept."
        assert self.tool._extract_severity(response) == "Critical"


class TestStudentWorkAnalyzerUse:
    """Tests for the main use() method."""

    def test_valid_json_input(self):
        llm_response = (
            "CORRECT_ASPECTS: Student applied the formula\n"
            "ERROR_IDENTIFIED: None\n"
            "ROOT_MISCONCEPTION: None\n"
            "SEVERITY: Minor\n"
            "SUGGESTED_FOCUS: Continue practice\n"
            "EVIDENCE: Student wrote p = mv correctly"
        )
        llm = MockLLM(llm_response)
        retriever = MockRetriever(documents=["Momentum is p = mv"])
        tool = StudentWorkAnalyzerTool(llm=llm, retriever=retriever)

        tool_input = build_json_input(
            DiagnosticInput,
            problem="Calculate momentum",
            student_work="p = 5 * 10 = 50 kg m/s",
            topic="physics"
        )

        result = tool.use(tool_input)
        assert "ANALYSIS COMPLETE" in result
        assert "Minor" in result

    def test_invalid_json_returns_error(self):
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )
        result = tool.use("not valid json")
        assert "ERROR" in result

    def test_missing_parts_returns_error(self):
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )
        result = tool.use('{"problem": "some problem"}')
        assert "ERROR" in result

    def test_retriever_called_with_top_k(self):
        """Verify retriever uses top_k parameter."""
        retriever = MockRetriever(documents=["doc1", "doc2", "doc3"])
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM("SEVERITY: Minor\nAnalysis complete."),
            retriever=retriever
        )

        tool_input = build_json_input(
            DiagnosticInput,
            problem="Find x",
            student_work="x = 5",
            topic="algebra"
        )

        tool.use(tool_input)
        assert retriever.last_query is not None
        assert retriever.last_top_k == 3

    def test_empty_retriever_results_handled(self):
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM("SEVERITY: Major\nNo course context available."),
            retriever=MockRetriever(documents=[])
        )

        tool_input = build_json_input(
            DiagnosticInput,
            problem="Find derivative",
            student_work="dy/dx = 2x",
            topic="calculus"
        )

        result = tool.use(tool_input)
        assert "ANALYSIS COMPLETE" in result

    def test_empty_problem_returns_error(self):
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )
        tool_input = build_json_input(
            DiagnosticInput,
            problem="",
            student_work="x=5",
            topic="algebra"
        )
        result = tool.use(tool_input)
        assert "ERROR" in result

    def test_empty_student_work_returns_error(self):
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )
        tool_input = build_json_input(
            DiagnosticInput,
            problem="Solve x+1=2",
            student_work="",
            topic="algebra"
        )
        result = tool.use(tool_input)
        assert "ERROR" in result

    def test_empty_topic_returns_error(self):
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )
        tool_input = build_json_input(
            DiagnosticInput,
            problem="Solve x+1=2",
            student_work="x=1",
            topic=""
        )
        result = tool.use(tool_input)
        assert "ERROR" in result

    def test_student_work_with_special_chars(self):
        """JSON handles special characters that would break ||| parsing."""
        llm = MockLLM("SEVERITY: Minor\nAll good.")
        tool = StudentWorkAnalyzerTool(llm=llm, retriever=MockRetriever())

        tool_input = build_json_input(
            DiagnosticInput,
            problem="Evaluate the ratio",
            student_work='The ratio is 2:3 and I think "maybe" it works',
            topic="math"
        )

        result = tool.use(tool_input)
        assert "ANALYSIS COMPLETE" in result
