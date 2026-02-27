"""Tests for DirectToolPlanner — zero-LLM-call planner for single-tool agents."""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fairlib.core.message import Action, FinalAnswer, Message, Thought
from fairlib.modules.planning.direct_planner import DirectToolPlanner


class TestDirectToolPlannerFirstCall:
    """First call (user_input non-empty): should return (Thought, Action)."""

    def test_returns_thought_action_tuple(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        result = planner.plan([], user_input="hello world")
        assert isinstance(result, tuple)
        thought, action = result
        assert isinstance(thought, Thought)
        assert isinstance(action, Action)

    def test_action_has_correct_tool_name(self):
        planner = DirectToolPlanner(tool_name="student_work_analyzer")
        _, action = planner.plan([], user_input="some input")
        assert action.tool_name == "student_work_analyzer"

    def test_action_passes_through_user_input(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        _, action = planner.plan([], user_input="exact input text")
        assert action.tool_input == "exact input text"

    def test_json_input_preserved(self):
        """JSON strings should pass through without modification."""
        planner = DirectToolPlanner(tool_name="my_tool")
        json_input = '{"problem": "Find x", "student_work": "x=5"}'
        _, action = planner.plan([], user_input=json_input)
        assert action.tool_input == json_input

    def test_async_returns_thought_action_tuple(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        result = asyncio.run(planner.aplan([], user_input="hello world"))
        assert isinstance(result, tuple)
        thought, action = result
        assert isinstance(thought, Thought)
        assert isinstance(action, Action)
        assert action.tool_name == "my_tool"
        assert action.tool_input == "hello world"


class TestDirectToolPlannerSecondCall:
    """Second call (user_input empty): should return FinalAnswer from observation."""

    def test_returns_final_answer(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        history = [
            Message(role="user", content="original request"),
            Message(role="system", content="Observation: The result is 42"),
        ]
        result = planner.plan(history, user_input="")
        assert isinstance(result, FinalAnswer)

    def test_extracts_observation_text(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        history = [
            Message(role="user", content="original request"),
            Message(role="system", content="Observation: The result is 42"),
        ]
        result = planner.plan(history, user_input="")
        assert result.text == "The result is 42"

    def test_uses_last_observation(self):
        """When multiple observations exist, use the last one."""
        planner = DirectToolPlanner(tool_name="my_tool")
        history = [
            Message(role="system", content="Observation: first result"),
            Message(role="system", content="Observation: second result"),
        ]
        result = planner.plan(history, user_input="")
        assert result.text == "second result"

    def test_multiline_observation(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        multiline = "Line 1\nLine 2\nLine 3"
        history = [
            Message(role="system", content=f"Observation: {multiline}"),
        ]
        result = planner.plan(history, user_input="")
        assert result.text == multiline

    def test_json_observation_preserved(self):
        """JSON output from tools should be preserved exactly."""
        planner = DirectToolPlanner(tool_name="my_tool")
        json_output = '{"misconception": "sign error", "severity": "Major"}'
        history = [
            Message(role="system", content=f"Observation: {json_output}"),
        ]
        result = planner.plan(history, user_input="")
        assert result.text == json_output

    def test_async_returns_final_answer(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        history = [
            Message(role="system", content="Observation: async result"),
        ]
        result = asyncio.run(planner.aplan(history, user_input=""))
        assert isinstance(result, FinalAnswer)
        assert result.text == "async result"


class TestDirectToolPlannerEdgeCases:
    """Edge cases and fallback behavior."""

    def test_empty_history_empty_input(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        result = planner.plan([], user_input="")
        assert isinstance(result, FinalAnswer)
        assert result.text == ""

    def test_no_observation_in_history_falls_back_to_last_message(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        history = [
            Message(role="user", content="some user message"),
            Message(role="assistant", content="some assistant message"),
        ]
        result = planner.plan(history, user_input="")
        assert isinstance(result, FinalAnswer)
        assert result.text == "some assistant message"

    def test_observation_with_empty_content(self):
        planner = DirectToolPlanner(tool_name="my_tool")
        history = [
            Message(role="system", content="Observation: "),
        ]
        result = planner.plan(history, user_input="")
        assert isinstance(result, FinalAnswer)
        assert result.text == ""
