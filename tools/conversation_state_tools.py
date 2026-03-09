"""Conversation state tracking tool — pure computation, no LLM calls.

Maintains structured state about problem progression across turns,
preventing context drift after memory compression.
"""

from pydantic import ValidationError

from fairlib.core.interfaces.tools import AbstractTool

from tools.schemas import ConversationStateAction, ConversationStateInput


class ProblemState:
    __slots__ = ("text", "status", "correct_turns")

    def __init__(self, text: str) -> None:
        self.text = text
        self.status: str = "active"
        self.correct_turns: int = 0


class ConversationStateTool(AbstractTool):
    """Tracks conversation state: current problem, solved problems, turn count.

    Two actions via JSON input:
      - get: Returns structured state summary
      - update: Modifies state (set_current_problem, mark_solved, etc.)

    Pure computation — no LLM call.
    """

    name = "conversation_state"
    description = (
        "Tracks conversation state across turns: current problem, solved problems, "
        "turn count, and consecutive correct turns. "
        'Input: JSON with "action" ("get" or "update"). '
        'For "update", optional fields: "set_current_problem" (problem_id), '
        '"problem_text" (text), "mark_solved" (problem_id), '
        '"increment_correct_turns" (bool), "reset_correct_turns" (bool). '
        "Returns structured state summary."
    )

    def __init__(self) -> None:
        self._current_problem_id: str | None = None
        self._problems: dict[str, ProblemState] = {}
        self._turn_count: int = 0

    def use(self, tool_input: str) -> str:
        try:
            inp = ConversationStateInput.model_validate_json(tool_input)
        except (ValueError, ValidationError):
            return (
                'ERROR: Invalid JSON input. Expected: '
                '{"action": "get"} or {"action": "update", "mark_solved": "problem_id"}'
            )

        if inp.action == ConversationStateAction.GET:
            return self._get_state()
        else:
            return self._update_state(inp)

    def _get_state(self) -> str:
        self._turn_count += 1

        lines = [f"Turn: {self._turn_count}"]

        if self._current_problem_id:
            prob = self._problems.get(self._current_problem_id)
            text = prob.text if prob else "unknown"
            lines.append(f"Current problem: {self._current_problem_id} — {text}")
            if prob:
                lines.append(f"Consecutive correct turns: {prob.correct_turns}")
        else:
            lines.append("Current problem: none")

        solved = [
            pid for pid, p in self._problems.items() if p.status == "solved"
        ]
        if solved:
            lines.append(f"Solved problems: {', '.join(solved)}")
        else:
            lines.append("Solved problems: none")

        return "\n".join(lines)

    def _update_state(self, inp: ConversationStateInput) -> str:
        changes: list[str] = []

        if inp.set_current_problem:
            self._current_problem_id = inp.set_current_problem
            if inp.set_current_problem not in self._problems:
                self._problems[inp.set_current_problem] = ProblemState(
                    text=inp.problem_text or inp.set_current_problem
                )
            changes.append(f"Current problem set to: {inp.set_current_problem}")

        if inp.mark_solved:
            if inp.mark_solved in self._problems:
                self._problems[inp.mark_solved].status = "solved"
            else:
                prob = ProblemState(text=inp.mark_solved)
                prob.status = "solved"
                self._problems[inp.mark_solved] = prob
            changes.append(f"Problem '{inp.mark_solved}' marked solved")

        if inp.increment_correct_turns and self._current_problem_id:
            prob = self._problems.get(self._current_problem_id)
            if prob:
                prob.correct_turns += 1
                changes.append(
                    f"Correct turns for '{self._current_problem_id}': {prob.correct_turns}"
                )

        if inp.reset_correct_turns and self._current_problem_id:
            prob = self._problems.get(self._current_problem_id)
            if prob:
                prob.correct_turns = 0
                changes.append(
                    f"Correct turns for '{self._current_problem_id}' reset to 0"
                )

        if not changes:
            return "No changes made."

        return "State updated. " + "; ".join(changes)
