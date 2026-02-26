"""Tests for agent creation and prompt construction."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM, MockRetriever


class TestManagerAgentPrompt:
    """Tests for TutorManagerAgent prompt construction."""

    def test_prompt_has_consistent_mode_names(self):
        """Verify no WORK_VALIDATION or QUESTION_ANSWERING mode names remain."""
        from agents.manager_agent import TutorManagerAgent

        builder = TutorManagerAgent._create_manager_prompt()

        role_text = builder.role_definition.text
        assert "WORK_VALIDATION" not in role_text
        assert "QUESTION_ANSWERING" not in role_text
        assert "HINT" in role_text
        assert "CONCEPT_EXPLANATION" in role_text

        for fi in builder.format_instructions:
            fi_text = fi.text
            assert "WORK_VALIDATION" not in fi_text
            assert "QUESTION_ANSWERING" not in fi_text

    def test_prompt_uses_json_delegation_format(self):
        """Verify delegation templates use JSON, not ||| format."""
        from agents.manager_agent import TutorManagerAgent

        builder = TutorManagerAgent._create_manager_prompt()

        # Check format instructions contain JSON examples
        all_fi_text = " ".join(fi.text for fi in builder.format_instructions)
        assert "|||" not in all_fi_text, "Format instructions still contain ||| delimiter"
        assert '"problem"' in all_fi_text or '"mode"' in all_fi_text

    def test_prompt_examples_use_json_delegation(self):
        """Verify examples use JSON delegation, not ||| format."""
        from agents.manager_agent import TutorManagerAgent

        builder = TutorManagerAgent._create_manager_prompt()

        for example in builder.examples:
            assert "|||" not in example.text, (
                f"Example still contains ||| delimiter: {example.text[:100]}"
            )

    def test_prompt_examples_are_domain_diverse(self):
        """Verify examples span multiple domains, not just physics/math."""
        from agents.manager_agent import TutorManagerAgent

        builder = TutorManagerAgent._create_manager_prompt()
        all_example_text = " ".join(e.text for e in builder.examples).lower()

        # Should have at least one non-STEM example
        non_stem_indicators = ["literature", "history", "essay", "theme", "novel", "war"]
        has_non_stem = any(ind in all_example_text for ind in non_stem_indicators)
        assert has_non_stem, "Examples should include non-STEM domains"

    def test_prompt_has_correct_routing_logic(self):
        """Verify work submission routes to HINT, questions to CONCEPT_EXPLANATION."""
        from agents.manager_agent import TutorManagerAgent

        builder = TutorManagerAgent._create_manager_prompt()
        role_text = builder.role_definition.text

        assert "submitting work" in role_text.lower() or "showing work" in role_text.lower()
        assert "guidance" in role_text.lower()

    def test_prompt_has_examples(self):
        from agents.manager_agent import TutorManagerAgent

        builder = TutorManagerAgent._create_manager_prompt()
        assert len(builder.examples) >= 2

    def test_prompt_role_definition_not_empty(self):
        from agents.manager_agent import TutorManagerAgent

        builder = TutorManagerAgent._create_manager_prompt()
        assert builder.role_definition is not None
        assert len(builder.role_definition.text) > 100


class TestMisconceptionDetectorPrompt:
    """Tests for MisconceptionDetectorAgent prompt construction."""

    def test_no_empty_examples(self):
        from agents.misconception_detector_agent import MisconceptionDetectorAgent

        builder = MisconceptionDetectorAgent._create_diagnostic_prompt()

        for example in builder.examples:
            assert example.text.strip() != "", \
                "Found empty example in MisconceptionDetector prompt"

    def test_has_role_definition(self):
        from agents.misconception_detector_agent import MisconceptionDetectorAgent

        builder = MisconceptionDetectorAgent._create_diagnostic_prompt()
        assert builder.role_definition is not None
        assert len(builder.role_definition.text) > 50

    def test_has_format_instructions(self):
        from agents.misconception_detector_agent import MisconceptionDetectorAgent

        builder = MisconceptionDetectorAgent._create_diagnostic_prompt()
        assert len(builder.format_instructions) > 0

    def test_uses_json_tool_input_format(self):
        """Verify tool input format instructions use JSON, not |||."""
        from agents.misconception_detector_agent import MisconceptionDetectorAgent

        builder = MisconceptionDetectorAgent._create_diagnostic_prompt()
        all_fi_text = " ".join(fi.text for fi in builder.format_instructions)
        assert "|||" not in all_fi_text, "Format instructions still contain ||| delimiter"


class TestHintGeneratorPrompt:
    """Tests for HintGeneratorAgent prompt construction."""

    def test_has_role_definition(self):
        from agents.hint_generator_agent import HintGeneratorAgent

        builder = HintGeneratorAgent._create_hint_prompt()
        assert builder.role_definition is not None
        assert len(builder.role_definition.text) > 50

    def test_has_format_instructions(self):
        from agents.hint_generator_agent import HintGeneratorAgent

        builder = HintGeneratorAgent._create_hint_prompt()
        assert len(builder.format_instructions) > 0

    def test_uses_json_tool_input_format(self):
        """Verify tool input format instructions use JSON, not |||."""
        from agents.hint_generator_agent import HintGeneratorAgent

        builder = HintGeneratorAgent._create_hint_prompt()
        all_fi_text = " ".join(fi.text for fi in builder.format_instructions)
        assert "|||" not in all_fi_text, "Format instructions still contain ||| delimiter"

    def test_examples_use_json(self):
        """Verify examples use JSON format."""
        from agents.hint_generator_agent import HintGeneratorAgent

        builder = HintGeneratorAgent._create_hint_prompt()
        for example in builder.examples:
            assert "|||" not in example.text, (
                f"Example still contains ||| delimiter: {example.text[:100]}"
            )


class TestSafetyGuardPrompt:
    """Tests for SafetyGuardAgent prompt construction."""

    def test_has_role_definition(self):
        from agents.safety_guard_agent import SafetyGuardAgent

        builder = SafetyGuardAgent._create_safety_prompt()
        assert builder.role_definition is not None
        assert len(builder.role_definition.text) > 50

    def test_uses_json_tool_input_format(self):
        """Verify tool input format instructions use JSON, not |||."""
        from agents.safety_guard_agent import SafetyGuardAgent

        builder = SafetyGuardAgent._create_safety_prompt()
        all_fi_text = " ".join(fi.text for fi in builder.format_instructions)
        assert "|||" not in all_fi_text, "Format instructions still contain ||| delimiter"

    def test_examples_use_json(self):
        """Verify examples use JSON format."""
        from agents.safety_guard_agent import SafetyGuardAgent

        builder = SafetyGuardAgent._create_safety_prompt()
        for example in builder.examples:
            assert "|||" not in example.text, (
                f"Example still contains ||| delimiter: {example.text[:100]}"
            )
