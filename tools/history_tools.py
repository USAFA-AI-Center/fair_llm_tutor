"""Student history checking tool — pure computation, no LLM calls."""

import json
import logging

from pydantic import ValidationError

from fairlib.core.interfaces.tools import AbstractTool

from tools.schemas import HistoryCheckInput

logger = logging.getLogger(__name__)


class CheckStudentHistoryTool(AbstractTool):
    """Checks whether the student has already provided the correct answer.

    Uses case-insensitive substring matching on student history entries.
    Pure text matching — no LLM call.
    """

    name = "check_student_history"
    description = (
        "Checks whether the student has already provided the correct answer "
        "in their conversation history. Pure text matching, no LLM. "
        'Input: JSON with "correct_answer" (str) and "student_history" (list of str). '
        "Returns whether any history entry matches the correct answer."
    )

    def use(self, tool_input: str) -> str:
        try:
            inp = HistoryCheckInput.model_validate_json(tool_input)
        except (ValueError, ValidationError):
            return (
                'ERROR: Invalid JSON input. Expected: '
                '{"correct_answer": "...", "student_history": ["..."]}'
            )

        if not inp.correct_answer.strip():
            return "STUDENT_ALREADY_ANSWERED: NO\nReason: No correct answer provided for comparison."

        correct_lower = inp.correct_answer.lower().strip()
        matching: list[str] = []

        for ans in inp.student_history:
            ans_lower = ans.lower().strip()
            if correct_lower in ans_lower or ans_lower in correct_lower:
                matching.append(ans)

        if matching:
            matched_str = "; ".join(matching)
            return (
                f"STUDENT_ALREADY_ANSWERED: YES\n"
                f"Matching answers: {matched_str}"
            )
        return "STUDENT_ALREADY_ANSWERED: NO"
