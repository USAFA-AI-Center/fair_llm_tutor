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

        # Check role definition
        role_text = builder.role_definition.text
        assert "WORK_VALIDATION" not in role_text
        assert "QUESTION_ANSWERING" not in role_text
        assert "MODE: HINT" in role_text
        assert "MODE: CONCEPT_EXPLANATION" in role_text

        # Check format instructions
        for fi in builder.format_instructions:
            fi_text = fi.text
            assert "WORK_VALIDATION" not in fi_text, \
                f"Found WORK_VALIDATION in format instruction: {fi_text[:100]}"
            assert "QUESTION_ANSWERING" not in fi_text, \
                f"Found QUESTION_ANSWERING in format instruction: {fi_text[:100]}"

    def test_prompt_has_correct_routing_logic(self):
        """Verify work submission routes to HINT, questions to CONCEPT_EXPLANATION."""
        from agents.manager_agent import TutorManagerAgent

        builder = TutorManagerAgent._create_manager_prompt()
        role_text = builder.role_definition.text

        # The text should say: submitting work → HINT mode
        assert "submitting work" in role_text.lower() or "showing work" in role_text.lower()
        assert "guidance" in role_text.lower()

        # Should NOT say submitting work → CONCEPT_EXPLANATION
        # The corrected line should have work→HINT and guidance→CONCEPT_EXPLANATION
        lines = role_text.split("\n")
        for line in lines:
            if "submitting work" in line.lower() and "MODE:" in line:
                assert "HINT" in line, f"Work submission should route to HINT, got: {line}"

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
        """Verify the empty Example('') bug is fixed."""
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


class TestSafetyGuardPrompt:
    """Tests for SafetyGuardAgent prompt construction."""

    def test_has_role_definition(self):
        from agents.safety_guard_agent import SafetyGuardAgent

        builder = SafetyGuardAgent._create_safety_prompt()
        assert builder.role_definition is not None
        assert len(builder.role_definition.text) > 50
