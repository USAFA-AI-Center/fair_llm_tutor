"""Tests for tools.hint_level_tools — pure computation, no LLM needed."""

import json
from tools.hint_level_tools import GetHintLevelTool, HINT_LEVEL_DESCRIPTIONS


class TestGetHintLevel:
    def setup_method(self):
        self.tool = GetHintLevelTool()

    def test_critical_maps_to_level_2(self):
        result = self.tool.use(json.dumps({"severity": "Critical"}))
        assert "Hint Level: 2" in result

    def test_major_maps_to_level_2(self):
        result = self.tool.use(json.dumps({"severity": "Major"}))
        assert "Hint Level: 2" in result

    def test_minor_maps_to_level_3(self):
        result = self.tool.use(json.dumps({"severity": "Minor"}))
        assert "Hint Level: 3" in result

    def test_unknown_severity_defaults_to_2(self):
        result = self.tool.use(json.dumps({"severity": "Unknown"}))
        assert "Hint Level: 2" in result

    def test_override_replaces_severity(self):
        result = self.tool.use(json.dumps({
            "severity": "Minor",
            "hint_level_override": 1,
        }))
        assert "Hint Level: 1" in result

    def test_override_clamped_low(self):
        result = self.tool.use(json.dumps({
            "severity": "Major",
            "hint_level_override": -5,
        }))
        assert "Hint Level: 1" in result

    def test_override_clamped_high(self):
        result = self.tool.use(json.dumps({
            "severity": "Major",
            "hint_level_override": 99,
        }))
        assert "Hint Level: 4" in result

    def test_includes_description(self):
        result = self.tool.use(json.dumps({"severity": "Minor"}))
        assert "Targeted Socratic question" in result

    def test_all_levels_have_descriptions(self):
        for level in range(1, 5):
            result = self.tool.use(json.dumps({
                "severity": "Major",
                "hint_level_override": level,
            }))
            assert HINT_LEVEL_DESCRIPTIONS[level] in result

    def test_invalid_json(self):
        result = self.tool.use("not json")
        assert "ERROR" in result

    def test_default_severity_is_major(self):
        result = self.tool.use(json.dumps({}))
        assert "Hint Level: 2" in result

    def test_case_insensitive_severity(self):
        result = self.tool.use(json.dumps({"severity": "CRITICAL"}))
        assert "Hint Level: 2" in result
        result = self.tool.use(json.dumps({"severity": "minor"}))
        assert "Hint Level: 3" in result
