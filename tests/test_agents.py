"""Tests for TutorAgent creation and prompt construction."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import MockLLM, MockRetriever


class TestTutorAgentCreation:
    """Tests for TutorAgent factory method and structural properties."""

    def test_uses_react_planner(self):
        from fairlib import WorkingMemory
        from fairlib.modules.planning.react_planner import SimpleReActPlanner
        from agents.tutor_agent import TutorAgent

        agent = TutorAgent.create(MockLLM(), WorkingMemory(), MockRetriever())
        assert isinstance(agent.planner, SimpleReActPlanner)

    def test_is_stateful(self):
        from fairlib import WorkingMemory
        from agents.tutor_agent import TutorAgent

        agent = TutorAgent.create(MockLLM(), WorkingMemory(), MockRetriever())
        assert agent.stateless is False

    def test_default_max_steps(self):
        from fairlib import WorkingMemory
        from agents.tutor_agent import TutorAgent

        agent = TutorAgent.create(MockLLM(), WorkingMemory(), MockRetriever())
        assert agent.max_steps == 10

    def test_custom_max_steps(self):
        from fairlib import WorkingMemory
        from agents.tutor_agent import TutorAgent

        agent = TutorAgent.create(
            MockLLM(), WorkingMemory(), MockRetriever(), max_steps=20
        )
        assert agent.max_steps == 20

    def test_has_tool_executor(self):
        from fairlib import WorkingMemory
        from fairlib.modules.action.executor import ToolExecutor
        from agents.tutor_agent import TutorAgent

        agent = TutorAgent.create(MockLLM(), WorkingMemory(), MockRetriever())
        assert isinstance(agent.tool_executor, ToolExecutor)

    def test_has_all_three_tools(self):
        from fairlib import WorkingMemory
        from agents.tutor_agent import TutorAgent

        agent = TutorAgent.create(MockLLM(), WorkingMemory(), MockRetriever())
        tool_names = set(agent.tool_executor.tool_registry.get_all_tools().keys())
        assert "student_work_analyzer" in tool_names
        assert "socratic_hint_generator" in tool_names
        assert "answer_revelation_analyzer" in tool_names

    def test_has_role_description(self):
        from fairlib import WorkingMemory
        from agents.tutor_agent import TutorAgent

        agent = TutorAgent.create(MockLLM(), WorkingMemory(), MockRetriever())
        assert agent.role_description
        assert len(agent.role_description) > 20


class TestTutorAgentPrompt:
    """Tests for TutorAgent prompt construction."""

    def _get_prompt(self):
        from agents.tutor_agent import TutorAgent
        return TutorAgent._create_prompt()

    def test_role_mentions_socratic(self):
        builder = self._get_prompt()
        assert "socratic" in builder.role_definition.text.lower()

    def test_role_mentions_never_reveal(self):
        builder = self._get_prompt()
        assert "never reveal" in builder.role_definition.text.lower()

    def test_role_mentions_domain_agnostic(self):
        builder = self._get_prompt()
        assert "domain-agnostic" in builder.role_definition.text.lower()

    def test_role_mentions_direct_address(self):
        builder = self._get_prompt()
        role_text = builder.role_definition.text.lower()
        assert "directly" in role_text or "second person" in role_text

    def test_has_format_instructions(self):
        builder = self._get_prompt()
        assert len(builder.format_instructions) >= 2

    def test_has_examples(self):
        builder = self._get_prompt()
        assert len(builder.examples) >= 2

    def test_examples_cover_hint_mode(self):
        builder = self._get_prompt()
        all_example_text = " ".join(e.text for e in builder.examples)
        assert "HINT" in all_example_text

    def test_examples_cover_concept_mode(self):
        builder = self._get_prompt()
        all_example_text = " ".join(e.text for e in builder.examples)
        assert "CONCEPT_EXPLANATION" in all_example_text

    def test_examples_are_domain_diverse(self):
        builder = self._get_prompt()
        all_example_text = " ".join(e.text for e in builder.examples).lower()
        non_stem_indicators = ["literature", "history", "essay", "theme", "novel"]
        has_non_stem = any(ind in all_example_text for ind in non_stem_indicators)
        assert has_non_stem, "Examples should include non-STEM domains"

    def test_no_old_agent_names_in_prompt(self):
        """Old multi-agent names must not appear in the prompt."""
        builder = self._get_prompt()

        all_text = builder.role_definition.text
        all_text += " ".join(fi.text for fi in builder.format_instructions)
        all_text += " ".join(e.text for e in builder.examples)

        for old_name in ["SafetyGuard", "MisconceptionDetector",
                         "HintGenerator", "delegate"]:
            assert old_name not in all_text, (
                f"Old agent name '{old_name}' found in prompt"
            )

    def test_all_tool_names_referenced(self):
        builder = self._get_prompt()
        all_text = builder.role_definition.text
        all_text += " ".join(fi.text for fi in builder.format_instructions)
        all_text += " ".join(e.text for e in builder.examples)

        for tool_name in ["student_work_analyzer", "socratic_hint_generator",
                          "answer_revelation_analyzer"]:
            assert tool_name in all_text, (
                f"Tool name '{tool_name}' not found in prompt"
            )
