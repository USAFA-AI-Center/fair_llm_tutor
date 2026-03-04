"""Hint level calculation tool — pure computation, no LLM calls."""

from pydantic import ValidationError

from fairlib.core.interfaces.tools import AbstractTool

from tools.schemas import HintLevelInput

HINT_LEVEL_DESCRIPTIONS = {
    1: "General conceptual reminder — very broad guidance",
    2: "Specific concept pointer — focus on the relevant concept",
    3: "Targeted Socratic question — guide toward the specific error",
    4: "Directed guidance — specific about what to check",
}

SEVERITY_TO_LEVEL = {
    "critical": 2,
    "major": 2,
    "minor": 3,
}


class GetHintLevelTool(AbstractTool):
    """Calculates the appropriate hint specificity level (1-4).

    Uses a deterministic severity-to-level mapping with optional override.
    Pure computation — no LLM call.
    """

    name = "get_hint_level"
    description = (
        "Calculates the appropriate hint specificity level (1-4) based on "
        "error severity and optional override. Pure computation, no LLM. "
        'Input: JSON with "severity" (Critical/Major/Minor) and optional '
        '"hint_level_override" (int 1-4). '
        "Returns the hint level with a description of the expected specificity."
    )

    def use(self, tool_input: str) -> str:
        try:
            inp = HintLevelInput.model_validate_json(tool_input)
        except (ValueError, ValidationError):
            return (
                'ERROR: Invalid JSON input. Expected: '
                '{"severity": "Major", "hint_level_override": null}'
            )

        # Deterministic severity → hint level mapping
        level = SEVERITY_TO_LEVEL.get(inp.severity.lower(), 2)

        # Apply override if provided (clamped to [1, 4])
        if inp.hint_level_override is not None:
            level = max(1, min(4, inp.hint_level_override))

        description = HINT_LEVEL_DESCRIPTIONS.get(level, HINT_LEVEL_DESCRIPTIONS[2])
        return f"Hint Level: {level}\nDescription: {description}"
