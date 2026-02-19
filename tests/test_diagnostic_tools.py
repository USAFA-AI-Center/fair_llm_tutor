"""Tests for diagnostic_tools.py — StudentWorkAnalyzerTool."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.diagnostic_tools import StudentWorkAnalyzerTool
from tests.conftest import MockLLM, MockRetriever, build_tool_input


class TestExtractUnitsFromWork:
    """Tests for _extract_units_from_work."""

    def setup_method(self):
        self.tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )

    def test_finds_kg_m_s_units(self):
        result = self.tool._extract_units_from_work("I got 50 kg m/s")
        assert len(result) >= 1

    def test_finds_newtons(self):
        result = self.tool._extract_units_from_work("The force is 100 N")
        assert len(result) >= 1

    def test_finds_joules(self):
        result = self.tool._extract_units_from_work("Energy = 200 J")
        assert len(result) >= 1

    def test_no_units_returns_empty(self):
        result = self.tool._extract_units_from_work("I think the answer is big")
        assert result == []

    def test_finds_meters_per_second(self):
        result = self.tool._extract_units_from_work("velocity is 25 m/s")
        assert len(result) >= 1


class TestCheckForMissingUnits:
    """Tests for _check_for_missing_units."""

    def setup_method(self):
        self.tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )

    def test_standalone_number_detected(self):
        assert self.tool._check_for_missing_units("50") is True

    def test_number_with_answer_keyword(self):
        assert self.tool._check_for_missing_units("answer = 50") is True

    def test_number_with_units_not_flagged(self):
        assert self.tool._check_for_missing_units("50 kg m/s") is False

    def test_text_without_numbers_not_flagged(self):
        assert self.tool._check_for_missing_units("I used the formula p = mv") is False


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

    def test_valid_three_part_input(self):
        llm_response = (
            "CORRECT_ASPECTS: Student applied the formula\n"
            "UNITS_CHECK: Present and correct\n"
            "ERROR_IDENTIFIED: None\n"
            "ROOT_MISCONCEPTION: None\n"
            "SEVERITY: Minor\n"
            "SUGGESTED_FOCUS: Continue practice\n"
            "EVIDENCE: Student wrote p = mv correctly"
        )
        llm = MockLLM(llm_response)
        retriever = MockRetriever(documents=["Momentum is p = mv"])
        tool = StudentWorkAnalyzerTool(llm=llm, retriever=retriever)

        tool_input = build_tool_input(
            PROBLEM="Calculate momentum",
            STUDENT_WORK="p = 5 * 10 = 50 kg m/s",
            TOPIC="physics"
        )

        result = tool.use(tool_input)
        assert "ANALYSIS COMPLETE" in result
        assert "Minor" in result

    def test_fewer_than_three_parts_returns_error(self):
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM(),
            retriever=MockRetriever()
        )
        result = tool.use("PROBLEM: some problem")
        assert "ERROR" in result

    def test_retriever_called_with_top_k(self):
        """Verify retriever uses top_k parameter (bug fix 1C)."""
        retriever = MockRetriever(documents=["doc1", "doc2", "doc3"])
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM("SEVERITY: Minor\nAnalysis complete."),
            retriever=retriever
        )

        tool_input = build_tool_input(
            PROBLEM="Find x",
            STUDENT_WORK="x = 5",
            TOPIC="algebra"
        )

        tool.use(tool_input)
        # Should have called retrieve with top_k, not k
        assert retriever.last_query is not None
        assert retriever.last_top_k == 3

    def test_empty_retriever_results_handled(self):
        tool = StudentWorkAnalyzerTool(
            llm=MockLLM("SEVERITY: Major\nNo course context available."),
            retriever=MockRetriever(documents=[])
        )

        tool_input = build_tool_input(
            PROBLEM="Find derivative",
            STUDENT_WORK="dy/dx = 2x",
            TOPIC="calculus"
        )

        result = tool.use(tool_input)
        assert "ANALYSIS COMPLETE" in result
