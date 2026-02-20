"""Tests for hint escalation (HINT_LEVEL override)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM, MockRetriever, build_tool_input


class TestHintLevelOverride:
    """HINT_LEVEL overrides severity-based hint level."""

    def _make_tool(self):
        from tools.pedagogical_tools import SocraticHintGeneratorTool
        return SocraticHintGeneratorTool(llm=MockLLM("Test hint"), retriever=MockRetriever())

    def test_hint_level_overrides_severity(self):
        """HINT_LEVEL: 4 should produce Level 4 even for Critical severity (default 2)."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Critical", TOPIC="algebra",
            HINT_LEVEL="4"
        ))
        assert "Level 4" in result

    def test_hint_level_1(self):
        """HINT_LEVEL: 1 should produce Level 1."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Major", TOPIC="algebra",
            HINT_LEVEL="1"
        ))
        assert "Level 1" in result

    def test_hint_level_clamped_to_max_4(self):
        """HINT_LEVEL: 10 should clamp to Level 4."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Minor", TOPIC="algebra",
            HINT_LEVEL="10"
        ))
        assert "Level 4" in result

    def test_hint_level_clamped_to_min_1(self):
        """HINT_LEVEL: 0 should clamp to Level 1."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Minor", TOPIC="algebra",
            HINT_LEVEL="0"
        ))
        assert "Level 1" in result

    def test_invalid_hint_level_ignored(self):
        """HINT_LEVEL: abc should be ignored, falling back to severity default."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Minor", TOPIC="algebra",
            HINT_LEVEL="abc"
        ))
        # Minor severity -> default Level 3
        assert "Level 3" in result

    def test_no_hint_level_uses_severity_default(self):
        """Without HINT_LEVEL, severity determines level as before."""
        tool = self._make_tool()
        result = tool.use(build_tool_input(
            MODE="HINT", PROBLEM="Solve 2x=10", STUDENT_WORK="x=3",
            MISCONCEPTION="division error", SEVERITY="Critical", TOPIC="algebra"
        ))
        # Critical -> default Level 2
        assert "Level 2" in result
