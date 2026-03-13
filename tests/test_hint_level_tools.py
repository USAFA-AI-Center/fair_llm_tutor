"""Tests for tools.hint_level_tools — pure computation, no LLM needed."""

import json
from tools.hint_level_tools import GetHintLevelTool, HINT_LEVEL_DESCRIPTIONS


class TestGetHintLevel:
    def setup_method(self):
        self.tool = GetHintLevelTool()

    def test_critical_maps_to_level_3(self):
        result = self.tool.use(json.dumps({"severity": "Critical"}))
        assert "Hint Level: 3" in result

    def test_major_maps_to_level_2(self):
        result = self.tool.use(json.dumps({"severity": "Major"}))
        assert "Hint Level: 2" in result

    def test_minor_maps_to_level_1(self):
        result = self.tool.use(json.dumps({"severity": "Minor"}))
        assert "Hint Level: 1" in result

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
        assert "Hint Level: 5" in result

    def test_level_5_override(self):
        result = self.tool.use(json.dumps({
            "severity": "Major",
            "hint_level_override": 5,
        }))
        assert "Hint Level: 5" in result
        assert "analogous example" in result.lower()

    def test_includes_description(self):
        result = self.tool.use(json.dumps({"severity": "Minor"}))
        assert "General conceptual reminder" in result

    def test_all_levels_have_descriptions(self):
        for level in range(1, 6):
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
        assert "Hint Level: 3" in result
        result = self.tool.use(json.dumps({"severity": "minor"}))
        assert "Hint Level: 1" in result


class TestHintEscalation:
    """Tests for stateful hint escalation tracking."""

    def setup_method(self):
        self.tool = GetHintLevelTool()

    def test_first_hint_no_escalation(self):
        result = self.tool.use(json.dumps({
            "severity": "Major",
            "problem_id": "prob1",
        }))
        assert "Hint Level: 2" in result

    def test_second_hint_no_escalation(self):
        """Escalation threshold is 2, so 2nd hint stays at same level."""
        self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        result = self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        assert "Hint Level: 2" in result
        assert "Hint count for this problem: 2" in result

    def test_third_hint_escalates(self):
        """Default threshold is 2, so after 2 hints, 3rd hint escalates."""
        tool = GetHintLevelTool(escalation_threshold=2)
        for _ in range(2):
            tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        result = tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        assert "Hint Level: 3" in result
        assert "auto-escalated" in result

    def test_configurable_threshold(self):
        """Custom threshold of 4 should delay escalation."""
        tool = GetHintLevelTool(escalation_threshold=4)
        for _ in range(3):
            tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        result = tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        # 4th hint, threshold=4 → hint_count=3 → 3//4=0 → no escalation yet
        assert "Hint Level: 2" in result

    def test_escalation_caps_at_5(self):
        """Escalation should never go above level 5."""
        for _ in range(20):
            result = self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        assert "Hint Level: 5" in result

    def test_level_5_includes_escalation_guidance(self):
        """Level 5 should include guidance about worked analogous example."""
        tool = GetHintLevelTool(escalation_threshold=1)
        # With threshold=1, each call escalates: base=1 → 2 → 3 → 4 → 5
        for _ in range(4):
            tool.use(json.dumps({"severity": "Minor", "problem_id": "p"}))
        result = tool.use(json.dumps({"severity": "Minor", "problem_id": "p"}))
        assert "Hint Level: 5" in result
        assert "ESCALATION" in result

    def test_different_problems_independent(self):
        """Hint counts are tracked per problem."""
        for _ in range(3):
            self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        result = self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob2"}))
        assert "Hint Level: 2" in result

    def test_no_problem_id_no_escalation(self):
        """Without problem_id, no escalation tracking."""
        for _ in range(5):
            result = self.tool.use(json.dumps({"severity": "Major"}))
        assert "Hint Level: 2" in result
        assert "auto-escalated" not in result

    def test_reset_problem(self):
        """reset_problem clears hint count for a specific problem."""
        for _ in range(3):
            self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        self.tool.reset_problem("prob1")
        result = self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        assert "Hint Level: 2" in result

    def test_reset_all(self):
        """reset_all clears all hint counts."""
        for _ in range(3):
            self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        for _ in range(3):
            self.tool.use(json.dumps({"severity": "Minor", "problem_id": "prob2"}))
        self.tool.reset_all()
        r1 = self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        r2 = self.tool.use(json.dumps({"severity": "Minor", "problem_id": "prob2"}))
        assert "Hint Level: 2" in r1
        assert "Hint Level: 1" in r2


class TestMarkComplete:
    """Tests for mark_complete behavior."""

    def setup_method(self):
        self.tool = GetHintLevelTool()

    def test_mark_complete_resets_and_confirms(self):
        """mark_complete=True with problem_id resets hints and returns confirmation."""
        for _ in range(3):
            self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        result = self.tool.use(json.dumps({
            "mark_complete": True,
            "problem_id": "prob1",
        }))
        assert "marked complete" in result
        assert "prob1" in result

    def test_mark_complete_allows_fresh_start(self):
        """After mark_complete, next hint for same problem starts at base level."""
        for _ in range(5):
            self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        self.tool.use(json.dumps({
            "mark_complete": True,
            "problem_id": "prob1",
        }))
        result = self.tool.use(json.dumps({"severity": "Major", "problem_id": "prob1"}))
        assert "Hint Level: 2" in result

    def test_mark_complete_without_problem_id_gives_normal_hint(self):
        """mark_complete without problem_id falls through to normal hint calculation."""
        result = self.tool.use(json.dumps({
            "mark_complete": True,
            "severity": "Minor",
        }))
        assert "Hint Level: 1" in result

    def test_mark_complete_false_gives_normal_hint(self):
        """mark_complete=False should not trigger completion."""
        result = self.tool.use(json.dumps({
            "mark_complete": False,
            "severity": "Major",
            "problem_id": "prob1",
        }))
        assert "Hint Level: 2" in result
