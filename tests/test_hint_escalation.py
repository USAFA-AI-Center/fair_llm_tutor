"""Tests for hint escalation (hint_level override)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.schemas import HintInput, InteractionMode, Severity
from tests.conftest import MockLLM, MockRetriever, build_json_input


class TestHintLevelOverride:
    """hint_level overrides severity-based hint level."""

    def _make_tool(self):
        from tools.pedagogical_tools import SocraticHintGeneratorTool
        return SocraticHintGeneratorTool(llm=MockLLM("Test hint"), retriever=MockRetriever())

    def test_hint_level_overrides_severity(self):
        """hint_level=4 should produce Level 4 even for Critical severity (default 2)."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="division error", severity=Severity.CRITICAL, topic="algebra",
            hint_level=4
        ))
        assert "Level 4" in result

    def test_hint_level_1(self):
        """hint_level=1 should produce Level 1."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="division error", severity=Severity.MAJOR, topic="algebra",
            hint_level=1
        ))
        assert "Level 1" in result

    def test_hint_level_clamped_to_max_4(self):
        """hint_level=10 should clamp to Level 4."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="division error", severity=Severity.MINOR, topic="algebra",
            hint_level=10
        ))
        assert "Level 4" in result

    def test_hint_level_clamped_to_min_1(self):
        """hint_level=0 should clamp to Level 1."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="division error", severity=Severity.MINOR, topic="algebra",
            hint_level=0
        ))
        assert "Level 1" in result

    def test_no_hint_level_uses_severity_default(self):
        """Without hint_level, severity determines level as before."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="division error", severity=Severity.CRITICAL, topic="algebra"
        ))
        # Critical -> default Level 2
        assert "Level 2" in result

    def test_minor_severity_default_level(self):
        """Minor severity without override -> Level 3."""
        tool = self._make_tool()
        result = tool.use(build_json_input(
            HintInput,
            mode=InteractionMode.HINT, problem="Solve 2x=10", student_work="x=3",
            misconception="division error", severity=Severity.MINOR, topic="algebra"
        ))
        assert "Level 3" in result
