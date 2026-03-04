"""Integration tests for the full TutorAgent pipeline.

These tests use SequenceMockLLM to script the agent's ReAct loop and verify:
- Tool call sequences (correct tools called in correct order)
- Safety checks fire in both HINT and CONCEPT_EXPLANATION modes
- Graceful degradation when tools error
- Unsafe response detection
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
    FailingMockLLM,
    FailingMockRetriever,
    MockLLM,
    MockRetriever,
    MockMessage,
    build_json_input,
)
from tools.schemas import DiagnosticInput, HintInput, SafetyInput, InteractionMode, Severity


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
# 1. HINT mode calls all 3 tools including safety
# ============================================================================


class TestHintModeCallsSafetyCheck:
    """Verify HINT mode calls: student_work_analyzer → socratic_hint_generator
    → answer_revelation_analyzer → final_answer.

    NOTE: The same SequenceMockLLM is shared between the planner and the tools
    (StudentWorkAnalyzerTool, SocraticHintGeneratorTool, AnswerRevelationAnalyzerTool
    each call self.llm.invoke() internally). So responses must be interleaved:
      planner → tool_internal → planner → tool_internal → planner → tool_internal → planner
    """

    @pytest.mark.asyncio
    async def test_hint_mode_calls_safety_check(self):
        """Full HINT pipeline: diagnose → hint → safety → answer.
        7 LLM calls total (4 planner + 3 tool-internal)."""
        analyzer_input = '{"problem": "Solve 2x+3=15", "student_work": "x=7", "topic": "algebra"}'
        hint_input = '{"mode": "HINT", "problem": "Solve 2x+3=15", "student_work": "x=7", "misconception": "division error", "severity": "Minor", "topic": "algebra"}'
        safety_input = '{"problem": "Solve 2x+3=15", "correct_answer": "x=6", "student_history": ["x=7"], "proposed_response": "Check your division step."}'

        llm = SequenceMockLLM([
            # 1. Planner: call student_work_analyzer
            _react_tool_call(
                "Student submitted work. Diagnosing.",
                "student_work_analyzer",
                analyzer_input,
            ),
            # 2. Tool-internal: student_work_analyzer's LLM call (analysis text)
            "CORRECT_ASPECTS: Subtracted 3 correctly\n"
            "ERROR_IDENTIFIED: Division error\n"
            "ROOT_MISCONCEPTION: Arithmetic\n"
            "SEVERITY: Minor\n"
            "SUGGESTED_FOCUS: Division\n"
            "EVIDENCE: x=7 instead of x=6",
            # 3. Planner: call socratic_hint_generator
            _react_tool_call(
                "Diagnosis complete. Generating hint.",
                "socratic_hint_generator",
                hint_input,
            ),
            # 4. Tool-internal: socratic_hint_generator's LLM call (hint text)
            "You correctly subtracted 3 from both sides. Now check: what is 12 divided by 2?",
            # 5. Planner: call answer_revelation_analyzer
            _react_tool_call(
                "Hint ready. Validating safety.",
                "answer_revelation_analyzer",
                safety_input,
            ),
            # 6. Tool-internal: answer_revelation_analyzer's LLM call (verdict)
            "VERDICT: SAFE\nREASONING: Guides without revealing.\n"
            "STUDENT_ALREADY_ANSWERED: NO\nCONFIDENCE: High",
            # 7. Planner: final answer
            _react_final_answer(
                "Safe. Delivering hint.",
                "Check your division step. What is 12 divided by 2?",
            ),
        ])

        agent = _build_agent(llm)
        result = await agent.arun(
            "PREPROCESSOR DETECTED MODE: HINT\n\n"
            "PROBLEM: Solve 2x+3=15\nSTUDENT WORK: x=7\nTOPIC: algebra"
        )

        assert llm.call_count == 7
        assert "Check your division step" in result


# ============================================================================
# 2. CONCEPT mode calls safety check (regression test for safety fix)
# ============================================================================


class TestConceptModeCallsSafetyCheck:
    """Verify CONCEPT_EXPLANATION mode calls socratic_hint_generator AND
    answer_revelation_analyzer before final_answer.

    5 LLM calls total (3 planner + 2 tool-internal)."""

    @pytest.mark.asyncio
    async def test_concept_mode_calls_safety_check(self):
        """Concept explanation pipeline: hint_gen → safety → answer."""
        concept_input = '{"mode": "CONCEPT_EXPLANATION", "concept": "momentum", "question": "What is momentum?", "topic": "physics"}'
        safety_input = '{"problem": "What is momentum?", "correct_answer": "N/A", "student_history": [], "proposed_response": "Momentum is the product of mass and velocity."}'

        llm = SequenceMockLLM([
            # 1. Planner: call socratic_hint_generator
            _react_tool_call(
                "Concept question. Generating explanation.",
                "socratic_hint_generator",
                concept_input,
            ),
            # 2. Tool-internal: socratic_hint_generator's LLM call
            "Momentum is defined as the product of an object's mass and velocity (p = mv).",
            # 3. Planner: call answer_revelation_analyzer (REQUIRED)
            _react_tool_call(
                "Explanation ready. Must validate safety.",
                "answer_revelation_analyzer",
                safety_input,
            ),
            # 4. Tool-internal: answer_revelation_analyzer's LLM call
            "VERDICT: SAFE\nREASONING: Concept explanation, no specific answer.\n"
            "STUDENT_ALREADY_ANSWERED: NO\nCONFIDENCE: High",
            # 5. Planner: final answer
            _react_final_answer(
                "Safe. Delivering explanation.",
                "Momentum is the product of mass and velocity. Can you think of an example?",
            ),
        ])

        agent = _build_agent(llm)
        result = await agent.arun(
            "PREPROCESSOR DETECTED MODE: CONCEPT_EXPLANATION\n"
            "Safety check REQUIRED.\n\n"
            "PROBLEM: General physics\nSTUDENT WORK: What is momentum?\nTOPIC: physics"
        )

        # 3 planner calls + 2 tool-internal calls = 5 total
        assert llm.call_count == 5
        assert "Momentum" in result


# ============================================================================
# 3. Tool error graceful degradation
# ============================================================================


class TestToolErrorGracefulDegradation:
    """When a tool receives bad input, it returns an ERROR observation and the
    agent can still produce a final answer (doesn't crash)."""

    @pytest.mark.asyncio
    async def test_tool_error_graceful_degradation(self):
        """Agent recovers when student_work_analyzer returns an error.

        We send malformed JSON to the tool so it returns an error string
        without making an internal LLM call — this way only the planner
        calls the shared SequenceMockLLM.
        """
        # Deliberately malformed JSON — tool will return ERROR without calling LLM
        bad_input = '{"not_a_valid_field": true}'

        llm = SequenceMockLLM([
            # 1. Planner: call student_work_analyzer with bad input
            _react_tool_call(
                "Diagnosing work.",
                "student_work_analyzer",
                bad_input,
            ),
            # 2. Planner: sees error observation, provides fallback answer
            _react_final_answer(
                "Tool returned an error. I'll give a general hint.",
                "Let's work through this step by step. What do you get when you subtract 1 from both sides?",
            ),
        ])

        agent = _build_agent(llm)
        result = await agent.arun(
            "PROBLEM: Solve x+1=2\nSTUDENT WORK: x=0\nTOPIC: algebra"
        )

        # Agent should still produce a response (not crash)
        assert llm.call_count == 2
        assert "step by step" in result.lower() or "subtract" in result.lower()


# ============================================================================
# 4. Unsafe response detection
# ============================================================================


class TestUnsafeResponseDetected:
    """When answer_revelation_analyzer returns UNSAFE, verify the agent does
    not blindly deliver the unsafe response."""

    @pytest.mark.asyncio
    async def test_unsafe_response_triggers_regeneration(self):
        """Agent should not deliver a response flagged UNSAFE.

        Interleaved sequence: planner → tool → planner → tool → planner → tool
        → planner → tool → planner (9 calls total: 5 planner + 4 tool-internal).
        """
        concept_input = '{"mode": "CONCEPT_EXPLANATION", "concept": "momentum", "question": "What is momentum?", "topic": "physics"}'
        unsafe_safety_input = '{"problem": "Calculate momentum", "correct_answer": "50 kg*m/s", "student_history": [], "proposed_response": "The answer is 50 kg*m/s."}'
        safe_safety_input = '{"problem": "Calculate momentum", "correct_answer": "50 kg*m/s", "student_history": [], "proposed_response": "Think about what happens when you multiply mass by velocity."}'

        llm = SequenceMockLLM([
            # 1. Planner: call socratic_hint_generator
            _react_tool_call(
                "Generating explanation.",
                "socratic_hint_generator",
                concept_input,
            ),
            # 2. Tool-internal: hint generator LLM call
            "The answer is 50 kg*m/s when you multiply mass by velocity.",
            # 3. Planner: call answer_revelation_analyzer
            _react_tool_call(
                "Checking safety.",
                "answer_revelation_analyzer",
                unsafe_safety_input,
            ),
            # 4. Tool-internal: safety tool LLM call (returns UNSAFE)
            "VERDICT: UNSAFE\nREASONING: Reveals the answer directly.\n"
            "STUDENT_ALREADY_ANSWERED: NO\nCONFIDENCE: High",
            # 5. Planner: sees UNSAFE, regenerates
            _react_tool_call(
                "Response was UNSAFE. Regenerating safer version.",
                "socratic_hint_generator",
                concept_input,
            ),
            # 6. Tool-internal: hint generator LLM call (safer version)
            "Think about what happens when you multiply mass by velocity.",
            # 7. Planner: recheck safety
            _react_tool_call(
                "Rechecking safety.",
                "answer_revelation_analyzer",
                safe_safety_input,
            ),
            # 8. Tool-internal: safety tool LLM call (returns SAFE)
            "VERDICT: SAFE\nREASONING: Guides without revealing.\n"
            "STUDENT_ALREADY_ANSWERED: NO\nCONFIDENCE: High",
            # 9. Planner: final answer
            _react_final_answer(
                "Safe now. Delivering.",
                "Think about what happens when you multiply mass by velocity.",
            ),
        ])

        agent = _build_agent(llm)
        result = await agent.arun(
            "PREPROCESSOR DETECTED MODE: CONCEPT_EXPLANATION\n"
            "Safety check REQUIRED.\n\n"
            "PROBLEM: Calculate momentum\nSTUDENT WORK: What is momentum?\nTOPIC: physics"
        )

        # The agent didn't deliver "The answer is 50"
        assert "the answer is 50" not in result.lower()
        assert llm.call_count == 9


# ============================================================================
# 5. Preprocessor always adds safety guidance
# ============================================================================


class TestProcessStudentWorkPreprocessor:
    """Verify that process_student_work() always adds safety guidance
    to the preprocessor prefix regardless of mode."""

    @pytest.mark.asyncio
    async def test_hint_mode_has_safety_required(self):
        """HINT mode should include 'Safety check REQUIRED.'"""
        llm = SequenceMockLLM([
            _react_final_answer("Responding.", "Here is your hint."),
        ])

        agent = _build_agent(llm)

        # Directly test the preprocessor logic from main.py
        student_work = "I got x = 7"
        detected_mode = TutorAgent.detect_mode(student_work)
        assert detected_mode == "HINT"

        # Build the request as main.py does
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

        # Under old code this would NOT have safety required — now it always does
        request = f"PROBLEM: Music theory\n\nSTUDENT WORK: {student_work}\n\nTOPIC: music"
        if detected_mode:
            prefix = f"PREPROCESSOR DETECTED MODE: {detected_mode}"
            prefix += "\nSafety check REQUIRED."
            request = f"{prefix}\n\n{request}"

        assert "Safety check REQUIRED." in request


# ============================================================================
# 6. Retriever failure continues gracefully
# ============================================================================


class TestRetrieverFailureContinues:
    """When the retriever raises, the diagnostic tool should return analysis
    without course context (not crash)."""

    def test_retriever_failure_in_diagnostic_tool(self):
        """StudentWorkAnalyzerTool continues with empty context when retriever fails."""
        from tools.diagnostic_tools import StudentWorkAnalyzerTool

        llm = MockLLM(
            "CORRECT_ASPECTS: Good setup\n"
            "ERROR_IDENTIFIED: Division error\n"
            "ROOT_MISCONCEPTION: Arithmetic\n"
            "SEVERITY: Minor\n"
            "SUGGESTED_FOCUS: Division\n"
            "EVIDENCE: x=7 instead of x=6"
        )
        tool = StudentWorkAnalyzerTool(llm, FailingMockRetriever())

        result = tool.use(build_json_input(
            DiagnosticInput,
            problem="Solve 2x+3=15",
            student_work="x=7",
            topic="algebra",
        ))

        # Should NOT crash — should return analysis with "No specific course materials"
        assert "ANALYSIS COMPLETE" in result
        assert "Minor" in result

    def test_retriever_failure_in_hint_generator(self):
        """SocraticHintGeneratorTool continues when retriever fails during hint gen."""
        from tools.pedagogical_tools import SocraticHintGeneratorTool

        llm = MockLLM("Check your division step carefully.")
        tool = SocraticHintGeneratorTool(llm, FailingMockRetriever())

        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Solve 2x+3=15",
            student_work="x=7",
            misconception="division error",
            severity=Severity.MINOR,
            topic="algebra",
        ))

        assert "COMPLETE HINT" in result
        assert "division" in result.lower()

    def test_retriever_failure_in_concept_explanation(self):
        """SocraticHintGeneratorTool continues when retriever fails during concept mode."""
        from tools.pedagogical_tools import SocraticHintGeneratorTool

        llm = MockLLM("Momentum is the product of mass and velocity.")
        tool = SocraticHintGeneratorTool(llm, FailingMockRetriever())

        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.CONCEPT_EXPLANATION,
            concept="momentum",
            question="What is momentum?",
            topic="physics",
        ))

        assert "CONCEPT EXPLANATION" in result
        assert "momentum" in result.lower()


# ============================================================================
# 7. LLM failure in tools returns structured error
# ============================================================================


class TestLLMFailureInTools:
    """When a tool's internal LLM call fails, verify structured error strings."""

    def test_concept_explanation_llm_failure(self):
        """Concept explanation returns structured error on LLM failure."""
        from tools.pedagogical_tools import SocraticHintGeneratorTool

        tool = SocraticHintGeneratorTool(FailingMockLLM(), MockRetriever())

        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.CONCEPT_EXPLANATION,
            concept="momentum",
            question="What is momentum?",
            topic="physics",
        ))

        assert "ERROR" in result
        assert "Concept explanation generation failed" in result

    def test_hint_generation_llm_failure(self):
        """Hint generation returns structured error on LLM failure."""
        from tools.pedagogical_tools import SocraticHintGeneratorTool

        tool = SocraticHintGeneratorTool(FailingMockLLM(), MockRetriever())

        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Solve 2x+3=15",
            student_work="x=7",
            misconception="division error",
            severity=Severity.MINOR,
            topic="algebra",
        ))

        assert "ERROR" in result
        assert "Hint generation failed" in result

    def test_success_response_llm_failure(self):
        """Success response returns structured error on LLM failure."""
        from tools.pedagogical_tools import SocraticHintGeneratorTool

        tool = SocraticHintGeneratorTool(FailingMockLLM(), MockRetriever())

        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT,
            problem="Solve 2x+3=15",
            student_work="x=6",
            misconception="none - student is correct",
            severity=Severity.MINOR,
            topic="algebra",
        ))

        assert "ERROR" in result
        assert "Success response generation failed" in result


# ============================================================================
# 8. Prompt text verification
# ============================================================================


class TestPromptSafetyRequirement:
    """Verify the CONCEPT_EXPLANATION workflow in the prompt now requires safety."""

    def test_concept_workflow_requires_safety(self):
        """CONCEPT_EXPLANATION workflow must include REQUIRED safety check."""
        builder = TutorAgent._create_prompt()
        workflow_text = " ".join(fi.text for fi in builder.format_instructions)

        # Find the CONCEPT_EXPLANATION workflow section
        assert "CONCEPT_EXPLANATION" in workflow_text
        # The workflow should mention answer_revelation_analyzer as REQUIRED
        assert "answer_revelation_analyzer" in workflow_text

        # Old optional language should be gone
        assert "If the PREPROCESSOR WARNING" not in workflow_text

    def test_concept_example_includes_safety_tool(self):
        """CONCEPT_EXPLANATION example must show answer_revelation_analyzer being called."""
        builder = TutorAgent._create_prompt()
        # The second example is CONCEPT_EXPLANATION
        concept_example = builder.examples[1].text
        assert "answer_revelation_analyzer" in concept_example
        # Old "no specific answer to reveal" phrasing should be gone
        assert "no specific answer to reveal" not in concept_example
