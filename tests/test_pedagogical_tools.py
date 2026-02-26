"""Tests for pedagogical_tools.py — SocraticHintGeneratorTool."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.pedagogical_tools import SocraticHintGeneratorTool
from tools.schemas import HintInput, InteractionMode, Severity
from tests.conftest import MockLLM, MockRetriever, build_json_input


class TestSocraticHintGeneratorParsing:
    """Tests for input parsing and mode routing."""

    def test_hint_mode_default(self):
        """Default mode should be HINT when MODE specified."""
        llm = MockLLM("Here is a helpful hint about your work.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Find x in 2x = 10",
            student_work="x = 3",
            misconception="Arithmetic error",
            severity=Severity.MINOR,
            topic="algebra"
        )

        result = tool.use(tool_input)
        assert "COMPLETE HINT" in result

    def test_concept_explanation_mode(self):
        """MODE: CONCEPT_EXPLANATION should route to concept explanation."""
        llm = MockLLM("Momentum is mass times velocity.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.CONCEPT_EXPLANATION,
            concept="momentum",
            question="What is momentum?",
            topic="physics"
        )

        result = tool.use(tool_input)
        assert "CONCEPT EXPLANATION" in result

    def test_hint_mode_explicit(self):
        """MODE: HINT should generate a hint."""
        llm = MockLLM("Think about what happens when you multiply.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Calculate 5 * 10",
            student_work="I got 55",
            misconception="Addition instead of multiplication",
            severity=Severity.MAJOR,
            topic="math"
        )

        result = tool.use(tool_input)
        assert "COMPLETE HINT" in result

    def test_invalid_json_returns_error(self):
        llm = MockLLM("hint")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())
        result = tool.use("not json")
        assert "ERROR" in result


class TestCorrectAnswerDetection:
    """Tests for when student has the correct answer."""

    def test_none_misconception_triggers_success(self):
        llm = MockLLM("Great job! Your answer is correct.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="What is 2+2?",
            student_work="4",
            misconception="None - correct answer",
            severity=Severity.MINOR,
            topic="math"
        )

        result = tool.use(tool_input)
        assert "SUCCESS RESPONSE" in result

    def test_correct_misconception_triggers_success(self):
        llm = MockLLM("Well done!")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Solve for x",
            student_work="x = 5",
            misconception="Student is correct",
            severity=Severity.MINOR,
            topic="algebra"
        )

        result = tool.use(tool_input)
        assert "SUCCESS RESPONSE" in result


class TestHintLevelMapping:
    """Tests for severity to hint level mapping."""

    def test_critical_severity_maps_to_level_2(self):
        llm = MockLLM("Think about the fundamental concept.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Calculate force",
            student_work="F = 50",
            misconception="Wrong formula used",
            severity=Severity.CRITICAL,
            topic="physics"
        )

        result = tool.use(tool_input)
        assert "Level 2" in result

    def test_minor_severity_maps_to_level_3(self):
        llm = MockLLM("Check your arithmetic in the last step.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Calculate 12 * 3",
            student_work="I got 34",
            misconception="Small calculation error",
            severity=Severity.MINOR,
            topic="math"
        )

        result = tool.use(tool_input)
        assert "Level 3" in result


class TestRetrieverIntegration:
    """Tests for RAG integration in hint generation."""

    def test_retriever_failure_gracefully_handled(self):
        """When retriever raises, tool should still generate a hint."""

        class FailingRetriever:
            def retrieve(self, query, top_k=3):
                raise RuntimeError("Database connection failed")

        llm = MockLLM("Think about the definition of momentum.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=FailingRetriever())

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Calculate momentum",
            student_work="p = 50",
            misconception="Missing units",
            severity=Severity.MINOR,
            topic="physics"
        )

        result = tool.use(tool_input)
        # Should still produce a hint even without RAG context
        assert "COMPLETE HINT" in result

    def test_none_retriever_handled(self):
        """When retriever is None, should still work."""
        llm = MockLLM("Let me explain this concept.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=None)

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.CONCEPT_EXPLANATION,
            concept="derivatives",
            question="What is a derivative?",
            topic="calculus"
        )

        result = tool.use(tool_input)
        assert "CONCEPT EXPLANATION" in result

    def test_retriever_with_docs_used(self):
        """Verify retriever documents are passed to LLM prompt."""
        retriever = MockRetriever(documents=[
            "The derivative of x^n is n*x^(n-1)."
        ])
        llm = MockLLM("The power rule helps here.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=retriever)

        tool_input = build_json_input(
            HintInput,
            mode=InteractionMode.CONCEPT_EXPLANATION,
            concept="power rule",
            question="How does the power rule work?",
            topic="calculus"
        )

        tool.use(tool_input)
        # Verify retriever was called
        assert retriever.last_query is not None
        assert "power rule" in retriever.last_query
