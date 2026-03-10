"""Hint level calculation tool — pure computation, no LLM calls.

Supports stateful hint escalation: tracks how many hints have been given
per problem and auto-escalates after repeated hints at the same level.
"""

from pydantic import ValidationError

from fairlib.core.interfaces.tools import AbstractTool

from tools.schemas import HintLevelInput

HINT_LEVEL_DESCRIPTIONS = {
    1: "General conceptual reminder — very broad guidance",
    2: "Specific concept pointer — focus on the relevant concept",
    3: "Targeted Socratic question — guide toward the specific error",
    4: "Directed guidance — specific about what to check",
    5: (
        "Worked analogous example — demonstrate the same concept with "
        "DIFFERENT values/context. Do NOT use the student's actual problem values."
    ),
}

SEVERITY_TO_LEVEL = {
    "critical": 2,
    "major": 2,
    "minor": 3,
}

# After this many hints at the same level, auto-escalate
_ESCALATION_THRESHOLD = 2


class GetHintLevelTool(AbstractTool):
    """Calculates the appropriate hint specificity level (1-5).

    Uses a deterministic severity-to-level mapping with optional override.
    Tracks hint counts per problem_id and auto-escalates after repeated hints.
    Pure computation — no LLM call.
    """

    name = "get_hint_level"
    description = (
        "Calculates the appropriate hint specificity level (1-5) based on "
        "error severity and optional override. Tracks hints per problem and "
        "auto-escalates after repeated hints at the same level. Level 5 provides "
        "a worked analogous example. Pure computation, no LLM. "
        'Input: JSON with "severity" (Critical/Major/Minor), optional '
        '"hint_level_override" (int 1-5), and optional "problem_id" (str). '
        "Returns the hint level with a description of the expected specificity."
    )

    def __init__(self, escalation_threshold: int = _ESCALATION_THRESHOLD) -> None:
        # problem_id -> total hint count for that problem
        self._problem_hint_counts: dict[str, int] = {}
        self._escalation_threshold = escalation_threshold

    def use(self, tool_input: str) -> str:
        try:
            inp = HintLevelInput.model_validate_json(tool_input)
        except (ValueError, ValidationError):
            return (
                'ERROR: Invalid JSON input. Expected: '
                '{"severity": "Major", "hint_level_override": null, "problem_id": null}'
            )

        # Handle mark_complete: reset the problem and return confirmation
        if inp.mark_complete and inp.problem_id:
            self.reset_problem(inp.problem_id)
            return f"Problem '{inp.problem_id}' marked complete. Hint count reset."

        # Deterministic severity → hint level mapping
        base_level = SEVERITY_TO_LEVEL.get(inp.severity.lower(), 2)

        # Apply override if provided (clamped to [1, 5])
        if inp.hint_level_override is not None:
            base_level = max(1, min(5, inp.hint_level_override))

        # Stateful escalation based on problem_id
        level = base_level
        hint_count = 0
        if inp.problem_id:
            hint_count = self._problem_hint_counts.get(inp.problem_id, 0)
            self._problem_hint_counts[inp.problem_id] = hint_count + 1

            # Auto-escalate: after threshold hints, bump level
            escalation_bumps = hint_count // self._escalation_threshold
            level = min(5, base_level + escalation_bumps)

        description = HINT_LEVEL_DESCRIPTIONS.get(level, HINT_LEVEL_DESCRIPTIONS[2])

        result = f"Hint Level: {level}\nDescription: {description}"
        if level == 5:
            result += (
                "\nESCALATION: Provide a worked example using DIFFERENT "
                "numbers/context. Do NOT use the student's actual problem values."
            )
        if inp.problem_id and hint_count > 0:
            result += f"\nHint count for this problem: {hint_count + 1}"
            if level > base_level:
                result += f" (auto-escalated from level {base_level})"
        return result

    def reset_problem(self, problem_id: str) -> None:
        """Reset hint count for a problem (e.g., when switching problems)."""
        self._problem_hint_counts.pop(problem_id, None)

    def reset_all(self) -> None:
        """Reset all hint counts."""
        self._problem_hint_counts.clear()
