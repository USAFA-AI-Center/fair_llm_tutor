# safety_tools.py

import logging

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message

from tools.schemas import SafetyInput

logger = logging.getLogger(__name__)

class AnswerRevelationAnalyzerTool(AbstractTool):
    """
    Uses LLM reasoning to determine if a response reveals an answer.

    Checks conversation history — if the student has previously given the
    correct answer, a response confirming it is marked SAFE.
    """

    name = "answer_revelation_analyzer"
    description = (
        "Analyzes if a proposed tutor response reveals the answer to a problem. "
        "Uses LLM reasoning, not pattern matching. Works for any domain. "
        'Input: JSON string with keys "problem", "correct_answer", '
        '"student_history" (list), "proposed_response".'
    )

    def __init__(self, llm: AbstractChatModel):
        self.llm = llm

    def use(self, tool_input: str) -> str:
        """
        Analyze if response reveals answer using LLM reasoning.
        """
        try:
            try:
                inp = SafetyInput.model_validate_json(tool_input)
            except Exception:
                return (
                    'ERROR: Invalid JSON input. Expected: '
                    '{"problem": "...", "correct_answer": "...", '
                    '"student_history": [...], "proposed_response": "..."}'
                )

            if not inp.proposed_response:
                return (
                    "ERROR: Missing required field: proposed_response"
                )

            # Check if student already provided the correct answer
            student_already_answered = False
            if inp.student_history and inp.correct_answer:
                correct_lower = inp.correct_answer.lower().strip()
                for ans in inp.student_history:
                    ans_lower = ans.lower().strip()
                    if correct_lower in ans_lower or ans_lower in correct_lower:
                        student_already_answered = True
                        break

            # Create reasoning prompt for LLM with history context
            history_desc = (
                f"The student has already provided these answers: {inp.student_history}"
                if inp.student_history
                else "The student has not provided any answers yet."
            )

            analysis_prompt = f"""You are a safety validator for a tutoring system. Your job is to determine if a proposed response reveals the answer to a problem.

IMPORTANT CONTEXT - STUDENT HISTORY:
{history_desc}
Student already stated the correct answer: {"YES" if student_already_answered else "NO"}

PROBLEM: {inp.problem}

CORRECT ANSWER (for your reference only): {inp.correct_answer}

PROPOSED RESPONSE TO VALIDATE: {inp.proposed_response}

CRITICAL RULE:
If the student has ALREADY stated the correct answer in their history, then it is SAFE to:
- Confirm their answer is correct
- Reference the specific value they provided
- Celebrate their success
- Use phrases like "Yes, your answer is correct!"

Otherwise, analyze carefully:
1. Does it state the final answer directly or indirectly?
2. Does it complete calculations that give away the answer?
3. Does it provide the last step that leads immediately to the answer?
4. Would a student who reads this response know the answer without thinking?

SAFE responses when student has NOT answered:
- Ask guiding questions (e.g., "What happens to the exponent?")
- Explain general concepts (e.g., "The power rule has two steps")
- Hint at approach (e.g., "Think about units")
- Identify errors without correcting (e.g., "Check your calculation")

UNSAFE responses when student has NOT answered:
- State the answer (e.g., "The answer is George Washington")
- Complete calculations (e.g., "5 * 10 = 50")
- Give the final step (e.g., "So you get 1998")

You MUST respond in this EXACT format:
VERDICT: [SAFE or UNSAFE]
REASONING: [Your explanation in 1-2 sentences]
STUDENT_ALREADY_ANSWERED: [YES or NO]
CONFIDENCE: [High, Medium, or Low]"""

            # Get LLM analysis
            messages = [Message(role="user", content=analysis_prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()

            # Parse and validate LLM response
            verdict = self._extract_verdict(result, student_already_answered)

            # Add structured prefix for agent parsing
            if verdict == "UNSAFE":
                return f"UNSAFE - Answer revelation detected.\n\n{result}"
            else:
                return f"SAFE - Response does not reveal answer.\n\n{result}"

        except Exception as e:
            logger.error(f"Safety analysis failed: {e}", exc_info=True)
            return f"ERROR: Analysis failed. {str(e)}"

    def _extract_verdict(self, llm_response: str, student_already_answered: bool) -> str:
        """
        Extract verdict from LLM response, considering student history.
        """
        for line in llm_response.split("\n"):
            if "VERDICT:" in line.upper():
                if "UNSAFE" in line.upper():
                    # Double-check: if student already answered, override to SAFE
                    if student_already_answered and "correct" in llm_response.lower():
                        return "SAFE"
                    return "UNSAFE"
                elif "SAFE" in line.upper():
                    return "SAFE"

        # If student already answered and response seems to confirm, it's SAFE
        if student_already_answered:
            confirm_phrases = ["correct", "right", "excellent", "perfect", "yes"]
            if any(phrase in llm_response.lower() for phrase in confirm_phrases):
                return "SAFE"

        # Fallback: search entire response
        response_upper = llm_response.upper()
        if "UNSAFE" in response_upper and not student_already_answered:
            return "UNSAFE"

        # Default to UNSAFE if unclear (conservative)
        return "UNSAFE"
