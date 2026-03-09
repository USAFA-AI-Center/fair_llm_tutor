"""Tests for tools.conversation_state_tools — pure computation, no LLM needed."""

import json

from tools.conversation_state_tools import ConversationStateTool


class TestConversationStateGet:
    def setup_method(self):
        self.tool = ConversationStateTool()

    def test_initial_state(self):
        result = self.tool.use(json.dumps({"action": "get"}))
        assert "Turn: 1" in result
        assert "Current problem: none" in result
        assert "Solved problems: none" in result

    def test_turn_increments(self):
        self.tool.use(json.dumps({"action": "get"}))
        result = self.tool.use(json.dumps({"action": "get"}))
        assert "Turn: 2" in result

    def test_shows_current_problem(self):
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "prob1",
            "problem_text": "Solve x + 1 = 2",
        }))
        result = self.tool.use(json.dumps({"action": "get"}))
        assert "prob1" in result
        assert "Solve x + 1 = 2" in result

    def test_shows_solved_problems(self):
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "prob1",
            "problem_text": "P1",
        }))
        self.tool.use(json.dumps({"action": "update", "mark_solved": "prob1"}))
        result = self.tool.use(json.dumps({"action": "get"}))
        assert "prob1" in result
        assert "Solved problems:" in result

    def test_shows_correct_turns(self):
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "prob1",
        }))
        self.tool.use(json.dumps({
            "action": "update",
            "increment_correct_turns": True,
        }))
        result = self.tool.use(json.dumps({"action": "get"}))
        assert "Consecutive correct turns: 1" in result


class TestConversationStateUpdate:
    def setup_method(self):
        self.tool = ConversationStateTool()

    def test_set_current_problem(self):
        result = self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "prob1",
            "problem_text": "Solve 2x = 4",
        }))
        assert "Current problem set to: prob1" in result

    def test_mark_solved(self):
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "prob1",
        }))
        result = self.tool.use(json.dumps({
            "action": "update",
            "mark_solved": "prob1",
        }))
        assert "marked solved" in result

    def test_mark_solved_unknown_problem(self):
        result = self.tool.use(json.dumps({
            "action": "update",
            "mark_solved": "unknown_prob",
        }))
        assert "marked solved" in result

    def test_increment_correct_turns(self):
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "prob1",
        }))
        result = self.tool.use(json.dumps({
            "action": "update",
            "increment_correct_turns": True,
        }))
        assert "Correct turns" in result
        assert "1" in result

    def test_reset_correct_turns(self):
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "prob1",
        }))
        self.tool.use(json.dumps({
            "action": "update",
            "increment_correct_turns": True,
        }))
        result = self.tool.use(json.dumps({
            "action": "update",
            "reset_correct_turns": True,
        }))
        assert "reset to 0" in result

    def test_no_changes(self):
        result = self.tool.use(json.dumps({"action": "update"}))
        assert "No changes made" in result

    def test_multiple_updates_at_once(self):
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "prob1",
        }))
        result = self.tool.use(json.dumps({
            "action": "update",
            "mark_solved": "prob1",
            "increment_correct_turns": True,
        }))
        assert "marked solved" in result

    def test_invalid_json(self):
        result = self.tool.use("not json at all")
        assert "ERROR" in result

    def test_invalid_action(self):
        result = self.tool.use(json.dumps({"action": "delete"}))
        assert "ERROR" in result


class TestConversationStateProgression:
    """Integration-style tests for multi-problem progression."""

    def setup_method(self):
        self.tool = ConversationStateTool()

    def test_full_problem_lifecycle(self):
        # Start problem
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "p1",
            "problem_text": "First problem",
        }))

        # Student gets it right
        self.tool.use(json.dumps({
            "action": "update",
            "increment_correct_turns": True,
        }))

        # Mark solved, start next
        self.tool.use(json.dumps({
            "action": "update",
            "mark_solved": "p1",
        }))
        self.tool.use(json.dumps({
            "action": "update",
            "set_current_problem": "p2",
            "problem_text": "Second problem",
        }))

        result = self.tool.use(json.dumps({"action": "get"}))
        assert "Current problem: p2" in result
        assert "p1" in result  # in solved list

    def test_solved_problems_accumulate(self):
        for i in range(3):
            pid = f"p{i}"
            self.tool.use(json.dumps({
                "action": "update",
                "set_current_problem": pid,
                "problem_text": f"Problem {i}",
            }))
            self.tool.use(json.dumps({
                "action": "update",
                "mark_solved": pid,
            }))

        result = self.tool.use(json.dumps({"action": "get"}))
        assert "p0" in result
        assert "p1" in result
        assert "p2" in result
