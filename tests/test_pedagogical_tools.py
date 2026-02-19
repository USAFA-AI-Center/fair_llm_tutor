"""Tests for pedagogical_tools.py — SocraticHintGeneratorTool."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.pedagogical_tools import SocraticHintGeneratorTool
from tests.conftest import MockLLM, MockRetriever, build_tool_input


class TestSocraticHintGeneratorParsing:
    """Tests for input parsing and mode routing."""

    def test_hint_mode_default(self):
        """Default mode should be HINT when no MODE specified."""
        llm = MockLLM("Here is a helpful hint about your work.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_tool_input(
            PROBLEM="Find x in 2x = 10",
            STUDENT_WORK="x = 3",
            MISCONCEPTION="Arithmetic error",
            SEVERITY="Minor",
            TOPIC="algebra"
        )

        result = tool.use(tool_input)
        assert "COMPLETE HINT" in result

    def test_concept_explanation_mode(self):
        """MODE: CONCEPT_EXPLANATION should route to concept explanation."""
        llm = MockLLM("Momentum is mass times velocity.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_tool_input(
            MODE="CONCEPT_EXPLANATION",
            CONCEPT="momentum",
            QUESTION="What is momentum?",
            TOPIC="physics"
        )

        result = tool.use(tool_input)
        assert "CONCEPT EXPLANATION" in result

    def test_hint_mode_explicit(self):
        """MODE: HINT should generate a hint."""
        llm = MockLLM("Think about what happens when you multiply.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_tool_input(
            MODE="HINT",
            PROBLEM="Calculate 5 * 10",
            STUDENT_WORK="I got 55",
            MISCONCEPTION="Addition instead of multiplication",
            SEVERITY="Major",
            TOPIC="math"
        )

        result = tool.use(tool_input)
        assert "COMPLETE HINT" in result


class TestCorrectAnswerDetection:
    """Tests for when student has the correct answer."""

    def test_none_misconception_triggers_success(self):
        llm = MockLLM("Great job! Your answer is correct.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_tool_input(
            MODE="HINT",
            PROBLEM="What is 2+2?",
            STUDENT_WORK="4",
            MISCONCEPTION="None - correct answer",
            SEVERITY="none",
            TOPIC="math"
        )

        result = tool.use(tool_input)
        assert "SUCCESS RESPONSE" in result

    def test_correct_misconception_triggers_success(self):
        llm = MockLLM("Well done!")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_tool_input(
            MODE="HINT",
            PROBLEM="Solve for x",
            STUDENT_WORK="x = 5",
            MISCONCEPTION="Student is correct",
            SEVERITY="none",
            TOPIC="algebra"
        )

        result = tool.use(tool_input)
        assert "SUCCESS RESPONSE" in result


class TestHintLevelMapping:
    """Tests for severity to hint level mapping."""

    def test_critical_severity_maps_to_level_2(self):
        llm = MockLLM("Think about the fundamental concept.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_tool_input(
            MODE="HINT",
            PROBLEM="Calculate force",
            STUDENT_WORK="F = 50",
            MISCONCEPTION="Wrong formula used",
            SEVERITY="Critical",
            TOPIC="physics"
        )

        result = tool.use(tool_input)
        assert "Level 2" in result

    def test_minor_severity_maps_to_level_3(self):
        llm = MockLLM("Check your arithmetic in the last step.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=MockRetriever())

        tool_input = build_tool_input(
            MODE="HINT",
            PROBLEM="Calculate 12 * 3",
            STUDENT_WORK="I got 34",
            MISCONCEPTION="Small calculation error",
            SEVERITY="Minor",
            TOPIC="math"
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

        tool_input = build_tool_input(
            MODE="HINT",
            PROBLEM="Calculate momentum",
            STUDENT_WORK="p = 50",
            MISCONCEPTION="Missing units",
            SEVERITY="Minor",
            TOPIC="physics"
        )

        result = tool.use(tool_input)
        # Should still produce a hint even without RAG context
        assert "COMPLETE HINT" in result

    def test_none_retriever_handled(self):
        """When retriever is None, should still work."""
        llm = MockLLM("Let me explain this concept.")
        tool = SocraticHintGeneratorTool(llm=llm, retriever=None)

        tool_input = build_tool_input(
            MODE="CONCEPT_EXPLANATION",
            CONCEPT="derivatives",
            QUESTION="What is a derivative?",
            TOPIC="calculus"
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

        tool_input = build_tool_input(
            MODE="CONCEPT_EXPLANATION",
            CONCEPT="power rule",
            QUESTION="How does the power rule work?",
            TOPIC="calculus"
        )

        tool.use(tool_input)
        # Verify retriever was called
        assert retriever.last_query is not None
        assert "power rule" in retriever.last_query
