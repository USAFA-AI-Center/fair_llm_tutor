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
    r"^(?:the answer is|the result is|the solution is|"
    r"my answer is|i got|i think it'?s?|i believe|"
    r"it should be|it equals|i calculated|"
    r"f'\(x\)\s*=|f\(x\)\s*=|x\s*=|y\s*=|p\s*=|v\s*=)\s*",
    re.IGNORECASE,
)

_NUMERIC_EPSILON = 1e-4

_OPERATOR_WHITESPACE = re.compile(r"\s*([+\-*/=^])\s*")
_MULTI_WHITESPACE = re.compile(r"\s+")


def _normalize_math(text: str) -> str:
    """Normalize a math expression for comparison.

    - Lowercase
    - Strip common answer prefixes
    - Remove whitespace around operators: '6x + 2' → '6x+2'
    - Collapse multiple spaces
    """
    t = text.lower().strip()
    t = _ANSWER_PREFIXES.sub("", t).strip()
    t = _OPERATOR_WHITESPACE.sub(r"\1", t)
    t = _MULTI_WHITESPACE.sub(" ", t).strip()
    return t


def _try_numeric_compare(a: str, b: str, epsilon: float = _NUMERIC_EPSILON) -> bool | None:
    """Try to parse both strings as floats and compare within epsilon.

    Returns True/False if both are numeric, None if either is not.
    """
    try:
        fa = float(a)
        fb = float(b)
        return abs(fa - fb) < epsilon
    except (ValueError, OverflowError):
        return None


def _compile_boundary(text: str) -> re.Pattern | None:
    """Compile a word-boundary pattern for *text*, or None if empty."""
    if not text:
        return None
    return re.compile(r'\b' + re.escape(text) + r'\b')


def _word_boundary_match(needle: str, haystack: str) -> bool:
    """Check if needle appears in haystack at word boundaries.

    For short answers (1-2 chars), require exact match or standalone
    occurrence to avoid false positives like "2" matching "2x".
    """
    if not needle or not haystack:
        return False
    # Exact match is always valid
    if needle == haystack:
        return True
    # Use word-boundary regex to prevent partial matches
    pattern = r'\b' + re.escape(needle) + r'\b'
    return bool(re.search(pattern, haystack))


class CheckStudentHistoryTool(AbstractTool):
    """Checks whether the student has already provided the correct answer.

    Uses math-aware normalization + word-boundary matching on student history entries.
    Pure text/numeric matching — no LLM call.
    """

    name = "check_student_history"
    description = (
        "Checks whether the student has already provided the correct answer "
        "in their conversation history. Uses math-aware normalization and "
        "word-boundary matching. No LLM. "
        'Input: JSON with "correct_answer" (str) and "student_history" (list of str). '
        "Returns whether any history entry matches the correct answer."
    )

    def __init__(self, epsilon: float = _NUMERIC_EPSILON) -> None:
        self._epsilon = epsilon

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

        # Pre-compile word-boundary patterns for the correct answer (avoid
        # recompilation on every history entry).
        correct_raw_re = _compile_boundary(correct_raw)
        correct_norm_re = _compile_boundary(correct_norm) if correct_norm else None

        for ans in inp.student_history:
            ans_raw = ans.lower().strip()
            ans_norm = _normalize_math(ans)

            # 1. Word-boundary match on raw values (check both directions)
            if correct_raw == ans_raw:
                matching.append(ans)
                continue
            if (correct_raw_re and correct_raw_re.search(ans_raw)) or \
               _word_boundary_match(ans_raw, correct_raw):
                matching.append(ans)
                continue

            # 2. Word-boundary match on normalized values (check both directions)
            if correct_norm and ans_norm:
                if correct_norm == ans_norm:
                    matching.append(ans)
                    continue
                if (correct_norm_re and correct_norm_re.search(ans_norm)) or \
                   _word_boundary_match(ans_norm, correct_norm):
                    matching.append(ans)
                    continue

            # 3. Numeric comparison
            numeric_result = _try_numeric_compare(
                correct_norm, ans_norm, self._epsilon
            )
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
