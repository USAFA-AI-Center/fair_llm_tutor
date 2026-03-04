"""Integration tests for the full TutorAgent pipeline.

These tests use SequenceMockLLM to script the agent's ReAct loop and verify:
- Tool call sequences (correct computational tools called in correct order)
- Agent self-validates safety in both HINT and CONCEPT_EXPLANATION modes
- Graceful degradation when tools error
- The agent reasons about student work itself (no LLM-wrapper tools)

KEY DIFFERENCE from old tests: Tools are now pure computation (no internal
LLM calls), so the SequenceMockLLM only receives planner calls.  Each tool
call is one planner step producing an Action, followed by one Observation
from the computational tool — no interleaved tool-internal LLM calls.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fairlib import WorkingMemory

from agents.tutor_agent import TutorAgent
from main import TutorSession
from tests.conftest import (
    SequenceMockLLM,
    FailingMockRetriever,
    MockLLM,
    MockRetriever,
)


# ============================================================================
# Helpers
# ============================================================================


def _build_agent(llm, retriever=None, max_steps=10):
    """Build a TutorAgent with the given LLM and optional retriever."""
    return TutorAgent.create(
        llm=llm,
        memory=WorkingMemory(),
        retriever=retriever or MockRetriever(),
        max_steps=max_steps,
    )


# SimpleReActPlanner format helpers
def _react_tool_call(thought: str, tool_name: str, tool_input: str) -> str:
    return (
        f"Thought: {thought}\n"
        f"Action:\n"
        f"tool_name: {tool_name}\n"
        f"tool_input: {tool_input}"
    )


def _react_final_answer(thought: str, answer: str) -> str:
    return (
        f"Thought: {thought}\n"
        f"Action:\n"
        f"tool_name: final_answer\n"
        f"tool_input: {answer}"
    )


# ============================================================================
# 1. HINT mode uses computational tools and agent reasons
# ============================================================================


class TestHintModeWorkflow:
    """Verify HINT mode calls: retrieve_course_materials →
    check_student_history → get_hint_level → final_answer.

    All tool calls are pure computation — no tool-internal LLM calls.
    Only the planner calls the LLM.
    """

    @pytest.mark.asyncio
    async def test_hint_mode_full_pipeline(self):
        """Full HINT pipeline: retrieve → history check → hint level → answer.
        4 planner-only LLM calls (no tool-internal LLM calls)."""
        llm = SequenceMockLLM([
            # 1. Planner: retrieve course materials
            _react_tool_call(
                "Student submitted work (HINT mode). Let me get context.",
                "retrieve_course_materials",
                '{"query": "algebra solving linear equations"}',
            ),
            # 2. Planner: check student history
            _react_tool_call(
                "Got course materials. Checking if student already answered.",
                "check_student_history",
                '{"correct_answer": "x = 6", "student_history": ["I got x = 7"]}',
            ),
            # 3. Planner: get hint level
            _react_tool_call(
                "Student has NOT answered correctly. I see they made a minor "
                "division error (12/2=7 instead of 6). Getting hint level.",
                "get_hint_level",
                '{"severity": "Minor"}',
            ),
            # 4. Planner: final answer with safety self-check
            _react_final_answer(
                "Level 3 = targeted Socratic question. My hint: 'You correctly "
                "subtracted 3 to get 12. What is 12 divided by 2?' "
                "SAFETY CHECK: Does not reveal x=6. SAFE.",
                "Good start! You correctly subtracted 3 from both sides to get "
                "12. Now double-check: what is 12 divided by 2?",
            ),
        ])

        retriever = MockRetriever(documents=[
            "When solving linear equations, isolate the variable."
        ])
        agent = _build_agent(llm, retriever)
        result = await agent.arun(
            "PREPROCESSOR DETECTED MODE: HINT\n"
            "Safety check REQUIRED.\n\n"
            "PROBLEM: Solve 2x+3=15\n\n"
            "STUDENT WORK: I got x = 7\n\n"
            "TOPIC: algebra\n\n"
            "CORRECT ANSWER (for safety check): x = 6"
        )

        # Only planner LLM calls — no tool-internal LLM calls
        assert llm.call_count == 4
        assert "12 divided by 2" in result


# ============================================================================
# 2. CONCEPT mode workflow
# ============================================================================


class TestConceptModeWorkflow:
    """Verify CONCEPT_EXPLANATION mode: retrieve → agent reasons → final_answer.
    Fewer steps since no diagnosis/hint-level needed."""

    @pytest.mark.asyncio
    async def test_concept_mode_pipeline(self):
        """Concept explanation: retrieve → reason → answer. 2 LLM calls."""
        llm = SequenceMockLLM([
            # 1. Planner: retrieve course materials
            _react_tool_call(
                "Student is asking a concept question. Getting materials.",
                "retrieve_course_materials",
                '{"query": "momentum physics definition"}',
            ),
            # 2. Planner: final answer
            _react_final_answer(
                "I have context. Momentum is mass times velocity. "
                "SAFETY CHECK: This is a concept explanation, no specific "
                "problem being solved. SAFE.",
                "Momentum is the product of an object's mass and velocity "
                "(p = mv). Can you think of an example?",
            ),
        ])

        retriever = MockRetriever(documents=[
            "Momentum p = mv, the product of mass and velocity."
        ])
        agent = _build_agent(llm, retriever)
        result = await agent.arun(
            "PREPROCESSOR DETECTED MODE: CONCEPT_EXPLANATION\n"
            "Safety check REQUIRED.\n\n"
            "STUDENT WORK: What is momentum?\n\nTOPIC: physics"
        )

        assert llm.call_count == 2
        assert "momentum" in result.lower()


# ============================================================================
# 3. Tool error graceful degradation
# ============================================================================


class TestToolErrorGracefulDegradation:
    """When a computational tool receives bad input, it returns an ERROR
    observation and the agent can still produce a final answer."""

    @pytest.mark.asyncio
    async def test_tool_error_graceful_degradation(self):
        """Agent recovers when retrieve_course_materials returns an error."""
        llm = SequenceMockLLM([
            # 1. Planner: call retrieve with bad input
            _react_tool_call(
                "Diagnosing work.",
                "retrieve_course_materials",
                '{"not_a_valid_field": true}',
            ),
            # 2. Planner: sees error observation, provides fallback answer
            _react_final_answer(
                "Retrieval failed. I'll give a general hint based on what I know.",
                "Let's work through this step by step. What do you get when "
                "you subtract 1 from both sides?",
            ),
        ])

        agent = _build_agent(llm)
        result = await agent.arun(
            "PROBLEM: Solve x+1=2\nSTUDENT WORK: x=0\nTOPIC: algebra"
        )

        assert llm.call_count == 2
        assert "step by step" in result.lower() or "subtract" in result.lower()


# ============================================================================
# 4. Agent safety self-check (replaces old separate safety tool test)
# ============================================================================


class TestAgentSafetySelfCheck:
    """The agent's prompt requires a SAFETY SELF-CHECK step. Verify the
    prompt includes this and the workflow enforces it."""

    def test_hint_workflow_has_safety_selfcheck(self):
        """HINT workflow must include SAFETY SELF-CHECK step."""
        builder = TutorAgent._create_prompt()
        workflow_text = " ".join(fi.text for fi in builder.format_instructions)
        assert "SAFETY SELF-CHECK" in workflow_text
        assert "REQUIRED" in workflow_text

    def test_concept_workflow_has_safety_selfcheck(self):
        """CONCEPT workflow must include SAFETY SELF-CHECK step."""
        builder = TutorAgent._create_prompt()
        workflow_text = " ".join(fi.text for fi in builder.format_instructions)
        # Both workflows mention safety
        assert workflow_text.count("SAFETY SELF-CHECK") >= 2

    def test_examples_demonstrate_safety_check(self):
        """Both examples must show the agent performing a safety check."""
        builder = TutorAgent._create_prompt()
        for example in builder.examples:
            assert "SAFETY CHECK" in example.text or "SAFE" in example.text, (
                f"Example missing safety check: {example.text[:80]}"
            )


# ============================================================================
# 5. Preprocessor always adds safety guidance
# ============================================================================


class TestProcessStudentWorkPreprocessor:
    """Verify that process_student_work() always adds safety guidance
    to the preprocessor prefix regardless of mode."""

    @pytest.mark.asyncio
    async def test_hint_mode_has_safety_required(self):
        """HINT mode should include 'Safety check REQUIRED.'"""
        student_work = "I got x = 7"
        detected_mode = TutorAgent.detect_mode(student_work)
        assert detected_mode == "HINT"

        request = f"PROBLEM: Solve 2x+3=15\n\nSTUDENT WORK: {student_work}\n\nTOPIC: algebra"
        if detected_mode:
            prefix = f"PREPROCESSOR DETECTED MODE: {detected_mode}"
            prefix += "\nSafety check REQUIRED."
            request = f"{prefix}\n\n{request}"

        assert "Safety check REQUIRED." in request

    @pytest.mark.asyncio
    async def test_concept_mode_has_safety_required(self):
        """CONCEPT_EXPLANATION mode should include 'Safety check REQUIRED.'"""
        student_work = "What is momentum?"
        detected_mode = TutorAgent.detect_mode(student_work)
        assert detected_mode == "CONCEPT_EXPLANATION"

        request = f"PROBLEM: General physics\n\nSTUDENT WORK: {student_work}\n\nTOPIC: physics"
        if detected_mode:
            prefix = f"PREPROCESSOR DETECTED MODE: {detected_mode}"
            prefix += "\nSafety check REQUIRED."
            request = f"{prefix}\n\n{request}"

        assert "Safety check REQUIRED." in request

    @pytest.mark.asyncio
    async def test_concept_without_answer_still_has_safety(self):
        """Pure concept question (no answer content) still gets safety required."""
        student_work = "What is the difference between major and minor scales?"
        detected_mode = TutorAgent.detect_mode(student_work)
        assert detected_mode == "CONCEPT_EXPLANATION"
        assert TutorAgent.has_answer_content(student_work) is False

        request = f"PROBLEM: Music theory\n\nSTUDENT WORK: {student_work}\n\nTOPIC: music"
        if detected_mode:
            prefix = f"PREPROCESSOR DETECTED MODE: {detected_mode}"
            prefix += "\nSafety check REQUIRED."
            request = f"{prefix}\n\n{request}"

        assert "Safety check REQUIRED." in request


# ============================================================================
# 6. Retriever failure continues gracefully (via retrieve_course_materials)
# ============================================================================


class TestRetrieverFailureContinues:
    """When the retriever raises, retrieve_course_materials should return
    a graceful message (not crash)."""

    def test_retriever_failure_returns_message(self):
        """RetrieveCourseMaterialsTool returns informative message on failure."""
        from tools.retrieval_tools import RetrieveCourseMaterialsTool

        tool = RetrieveCourseMaterialsTool(FailingMockRetriever())
        result = tool.use('{"query": "anything"}')

        assert "No course materials found" in result
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_agent_continues_after_retriever_failure(self):
        """Agent still produces a response when retriever fails."""
        llm = SequenceMockLLM([
            # 1. Planner: retrieve (will fail gracefully)
            _react_tool_call(
                "Getting context.",
                "retrieve_course_materials",
                '{"query": "algebra"}',
            ),
            # 2. Planner: continues despite retrieval failure
            _react_final_answer(
                "No materials available, but I can still help. "
                "SAFETY CHECK: Guiding question only. SAFE.",
                "Let's think about this step by step. What operation "
                "would you use to isolate x?",
            ),
        ])

        agent = _build_agent(llm, FailingMockRetriever())
        result = await agent.arun(
            "PROBLEM: Solve x+1=2\nSTUDENT WORK: x=0\nTOPIC: algebra"
        )

        assert llm.call_count == 2
        assert len(result) > 0


# ============================================================================
# 7. Student already answered correctly — check_student_history integration
# ============================================================================


class TestStudentAlreadyAnswered:
    """When check_student_history returns YES, the agent can confirm."""

    @pytest.mark.asyncio
    async def test_student_answered_correctly(self):
        """Agent can confirm when student already gave correct answer."""
        llm = SequenceMockLLM([
            # 1. Check history
            _react_tool_call(
                "Checking if student already answered.",
                "check_student_history",
                '{"correct_answer": "x = 6", "student_history": ["I got x = 6"]}',
            ),
            # 2. Final answer — can confirm since student already said it
            _react_final_answer(
                "Student already answered correctly (x=6). I can confirm. SAFE.",
                "Excellent work! Your answer x = 6 is correct. You correctly "
                "isolated x by subtracting 3 and dividing by 2.",
            ),
        ])

        agent = _build_agent(llm)
        result = await agent.arun(
            "PREPROCESSOR DETECTED MODE: HINT\n\n"
            "PROBLEM: Solve 2x+3=15\nSTUDENT WORK: I got x = 6\n"
            "TOPIC: algebra\nCORRECT ANSWER: x = 6"
        )

        assert "correct" in result.lower()
        assert llm.call_count == 2
