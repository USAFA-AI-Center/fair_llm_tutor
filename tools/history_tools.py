"""Student history checking tool — pure computation, no LLM calls.

Includes math-aware normalization for better answer matching:
- Whitespace normalization around operators
- Common prefix stripping (f'(x) =, the answer is, x =, etc.)
- Numeric comparison within epsilon
"""

import re

from pydantic import ValidationError

from fairlib.core.interfaces.tools import AbstractTool

from tools.schemas import HistoryCheckInput

# Prefixes to strip before comparison
_ANSWER_PREFIXES = re.compile(
    r"^(?:the answer is|my answer is|i got|i think it'?s?|"
    r"f'\(x\)\s*=|f\(x\)\s*=|x\s*=|y\s*=|p\s*=|v\s*=)\s*",
    re.IGNORECASE,
)

_NUMERIC_EPSILON = 1e-6


def _normalize_math(text: str) -> str:
    """Normalize a math expression for comparison.

    - Lowercase
    - Strip common answer prefixes
    - Remove whitespace around operators: '6x + 2' → '6x+2'
    - Collapse multiple spaces
    """
    t = text.lower().strip()
    t = _ANSWER_PREFIXES.sub("", t).strip()
    # Remove spaces around math operators
    t = re.sub(r"\s*([+\-*/=^])\s*", r"\1", t)
    # Collapse remaining whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _try_numeric_compare(a: str, b: str) -> bool | None:
    """Try to parse both strings as floats and compare within epsilon.

    Returns True/False if both are numeric, None if either is not.
    """
    try:
        fa = float(a)
        fb = float(b)
        return abs(fa - fb) < _NUMERIC_EPSILON
    except (ValueError, OverflowError):
        return None


class CheckStudentHistoryTool(AbstractTool):
    """Checks whether the student has already provided the correct answer.

    Uses math-aware normalization + substring matching on student history entries.
    Pure text/numeric matching — no LLM call.
    """

    name = "check_student_history"
    description = (
        "Checks whether the student has already provided the correct answer "
        "in their conversation history. Uses math-aware normalization and "
        "substring matching. No LLM. "
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

        correct_raw = inp.correct_answer.lower().strip()
        correct_norm = _normalize_math(inp.correct_answer)
        matching: list[str] = []

        for ans in inp.student_history:
            ans_raw = ans.lower().strip()
            ans_norm = _normalize_math(ans)

            # 1. Raw substring match (original behavior)
            if correct_raw in ans_raw or ans_raw in correct_raw:
                matching.append(ans)
                continue

            # 2. Normalized substring match
            if correct_norm and ans_norm:
                if correct_norm in ans_norm or ans_norm in correct_norm:
                    matching.append(ans)
                    continue

            # 3. Numeric comparison
            numeric_result = _try_numeric_compare(correct_norm, ans_norm)
            if numeric_result is True:
                matching.append(ans)
                continue

        if matching:
            matched_str = "; ".join(matching)
            return (
                f"STUDENT_ALREADY_ANSWERED: YES\n"
                f"Matching answers: {matched_str}"
            )
        return "STUDENT_ALREADY_ANSWERED: NO"
