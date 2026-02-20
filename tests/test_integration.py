"""
Integration tests: Config Manager round-trip with real tutor agents.

Tests the full lifecycle:
    Build tutor agents -> save config -> load config -> feed to optimizer -> bootstrap

Previous phases tested each repo in isolation with mocks.  These tests wire
the three repos together using the *actual* tutor agents (with mock LLMs so
no inference is needed).

Known gap documented here:
    config_manager._get_tool_registry() only registers SafeCalculatorTool,
    so custom tutor tools (AnswerRevelationAnalyzerTool, etc.) are skipped
    during load_multi_agent().  Prompts round-trip fine; tools don't.

Run:
    python -m pytest tests/test_integration.py -v
"""

import json
from pathlib import Path
from unittest.mock import patch

import dspy
import pytest

from fairlib.utils.config_manager import (
    extract_multi_agent_config,
    extract_prompts,
    load_agent_config,
    load_multi_agent,
    save_multi_agent_config,
)
from fair_prompt_optimizer import (
    MultiAgentOptimizer,
    OptimizedConfig,
    load_training_examples,
)
from fair_prompt_optimizer.optimizers.multi_agent import MultiAgentModule

from tests.conftest import MockLLM, MockRetriever, build_tutor_runner


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

TRAINING_DATA_PATH = str(
    Path(__file__).parent.parent / "training_data" / "examples.json"
)

EXPECTED_WORKERS = {"SafetyGuard", "MisconceptionDetector", "HintGenerator"}

EXPECTED_CUSTOM_TOOLS = {
    "AnswerRevelationAnalyzerTool",
    "StudentWorkAnalyzerTool",
    "SocraticHintGeneratorTool",
}


@pytest.fixture
def runner():
    """Build a full tutor runner for tests."""
    return build_tutor_runner()


@pytest.fixture
def config(runner):
    """Extract multi-agent config dict from the runner."""
    return extract_multi_agent_config(runner)


# ===========================================================================
# 1. TestConfigExtraction
# ===========================================================================


class TestConfigExtraction:
    """Verify extract_multi_agent_config(runner) produces correct structure."""

    def test_extract_produces_valid_structure(self, config):
        """Config has version, type, manager, workers, max_delegation_steps, metadata."""
        assert config["version"] == "1.0"
        assert config["type"] == "multi_agent"
        assert "manager" in config
        assert "workers" in config
        assert "max_delegation_steps" in config
        assert "metadata" in config

    def test_extract_has_all_three_workers(self, config):
        """Workers dict has the expected tutor worker keys."""
        assert set(config["workers"].keys()) == EXPECTED_WORKERS

    def test_manager_prompts_extracted(self, config):
        """Manager role_definition contains 'Socratic Tutor Manager'; has format_instructions and examples."""
        mgr_prompts = config["manager"]["prompts"]
        assert "Socratic Tutor Manager" in mgr_prompts["role_definition"]
        assert len(mgr_prompts["format_instructions"]) >= 2
        assert len(mgr_prompts["examples"]) >= 2

    def test_worker_prompts_extracted(self, config):
        """Each worker has a non-empty role_definition."""
        for name in EXPECTED_WORKERS:
            role_def = config["workers"][name]["prompts"]["role_definition"]
            assert role_def and len(role_def) > 0, f"{name} role_definition is empty"

    def test_custom_tools_listed_in_config(self, config):
        """Worker agent specs list the tutor's custom tool class names."""
        found_tools = set()
        for worker_config in config["workers"].values():
            for tool_name in worker_config["agent"]["tools"]:
                found_tools.add(tool_name)
        assert EXPECTED_CUSTOM_TOOLS.issubset(found_tools)


# ===========================================================================
# 2. TestConfigRoundTrip
# ===========================================================================


class TestConfigRoundTrip:
    """Save -> load -> compare.  Uses pytest tmp_path fixture."""

    def test_save_and_load_json(self, runner, tmp_path):
        """save_multi_agent_config writes valid JSON; load_agent_config reads it back."""
        path = str(tmp_path / "tutor_config.json")
        saved = save_multi_agent_config(runner, path)

        loaded = load_agent_config(path)
        assert loaded["type"] == "multi_agent"
        assert set(loaded["workers"].keys()) == EXPECTED_WORKERS
        # Top-level keys match
        assert set(saved.keys()) == set(loaded.keys())

    def test_manager_role_definition_survives_roundtrip(self, runner, tmp_path):
        """Manager role_definition text matches after save -> load_multi_agent."""
        original = extract_multi_agent_config(runner)
        orig_role = original["manager"]["prompts"]["role_definition"]

        path = str(tmp_path / "rt.json")
        save_multi_agent_config(runner, path)
        loaded_runner = load_multi_agent(path, MockLLM())

        loaded_config = extract_multi_agent_config(loaded_runner)
        assert loaded_config["manager"]["prompts"]["role_definition"] == orig_role

    def test_manager_format_instructions_survive_roundtrip(self, runner, tmp_path):
        """Format instructions text content matches after round-trip."""
        original = extract_multi_agent_config(runner)
        orig_fi = original["manager"]["prompts"]["format_instructions"]

        path = str(tmp_path / "rt.json")
        save_multi_agent_config(runner, path)
        loaded_runner = load_multi_agent(path, MockLLM())

        loaded_config = extract_multi_agent_config(loaded_runner)
        loaded_fi = loaded_config["manager"]["prompts"]["format_instructions"]

        # ManagerPlanner auto-merges mandatory format instructions on construction,
        # so the loaded runner may have additional format instructions.
        # Verify that all ORIGINAL instructions survive (content preserved).
        for orig_text in orig_fi:
            assert any(
                orig_text in loaded_text for loaded_text in loaded_fi
            ), f"Original format instruction not found after round-trip: {orig_text[:60]}..."

    def test_manager_examples_survive_roundtrip(self, runner, tmp_path):
        """Examples text content matches after round-trip."""
        original = extract_multi_agent_config(runner)
        orig_examples = original["manager"]["prompts"]["examples"]

        path = str(tmp_path / "rt.json")
        save_multi_agent_config(runner, path)
        loaded_runner = load_multi_agent(path, MockLLM())

        loaded_config = extract_multi_agent_config(loaded_runner)
        loaded_examples = loaded_config["manager"]["prompts"]["examples"]

        assert len(loaded_examples) == len(orig_examples)
        for orig, loaded in zip(orig_examples, loaded_examples):
            assert orig == loaded

    def test_worker_role_definitions_survive_roundtrip(self, runner, tmp_path):
        """All 3 workers' role_definitions match after round-trip."""
        original = extract_multi_agent_config(runner)

        path = str(tmp_path / "rt.json")
        save_multi_agent_config(runner, path)
        loaded_runner = load_multi_agent(path, MockLLM())
        loaded_config = extract_multi_agent_config(loaded_runner)

        for name in EXPECTED_WORKERS:
            orig_role = original["workers"][name]["prompts"]["role_definition"]
            loaded_role = loaded_config["workers"][name]["prompts"]["role_definition"]
            assert loaded_role == orig_role, f"{name} role_definition mismatch"

    def test_custom_tools_skipped_on_load(self, runner, tmp_path):
        """After load_multi_agent, workers' tool registries are empty (known gap).

        Documents that config_manager._get_tool_registry() doesn't know about
        tutor custom tools. Workers still have correct prompts.
        """
        path = str(tmp_path / "rt.json")
        save_multi_agent_config(runner, path)
        loaded_runner = load_multi_agent(path, MockLLM())

        for name, worker in loaded_runner.workers.items():
            tools = worker.planner.tool_registry.get_all_tools()
            assert len(tools) == 0, (
                f"{name} should have no tools after load (known gap), "
                f"but found: {list(tools.keys())}"
            )

            # Prompts are still preserved
            loaded_config = extract_multi_agent_config(loaded_runner)
            role_def = loaded_config["workers"][name]["prompts"]["role_definition"]
            assert role_def and len(role_def) > 0


# ===========================================================================
# 3. TestOptimizerIngestion
# ===========================================================================


class TestOptimizerIngestion:
    """Verify fair_prompt_optimizer can consume the tutor's config."""

    def test_export_creates_optimized_config(self, runner):
        """export_tutor_config returns OptimizedConfig with type=='multi_agent'."""
        from config_export import export_tutor_config

        opt_config = export_tutor_config(runner)
        assert isinstance(opt_config, OptimizedConfig)
        assert opt_config.type == "multi_agent"

    def test_config_has_manager_role(self, runner):
        """OptimizedConfig contains the manager's 'Socratic' role definition."""
        from config_export import export_tutor_config

        opt_config = export_tutor_config(runner)
        mgr_role = opt_config.config["manager"]["prompts"]["role_definition"]
        assert "Socratic" in mgr_role

    def test_optimizer_accepts_config(self, runner):
        """MultiAgentOptimizer(runner, config=opt_config) succeeds."""
        from config_export import export_tutor_config

        opt_config = export_tutor_config(runner)
        optimizer = MultiAgentOptimizer(runner, config=opt_config)
        assert optimizer.config.type == "multi_agent"

    def test_training_examples_load(self):
        """load_training_examples returns 8 examples, all with full_trace."""
        examples = load_training_examples(TRAINING_DATA_PATH)
        assert len(examples) == 8
        for ex in examples:
            assert ex.full_trace is not None and len(ex.full_trace) > 0

    def test_config_save_load_roundtrip(self, runner, tmp_path):
        """Save OptimizedConfig -> load via from_file -> verify prompts match."""
        from config_export import export_tutor_config

        opt_config = export_tutor_config(runner)
        path = str(tmp_path / "opt_config.json")
        opt_config.save(path)

        loaded = OptimizedConfig.from_file(path)
        assert loaded.type == "multi_agent"

        orig_role = opt_config.config["manager"]["prompts"]["role_definition"]
        loaded_role = loaded.config["manager"]["prompts"]["role_definition"]
        assert loaded_role == orig_role


# ===========================================================================
# 4. TestBootstrapIntegration
# ===========================================================================


class TestBootstrapIntegration:
    """Test optimizer bootstrap with tutor config.

    Patches MultiAgentModule.__call__ to avoid real LLM calls.
    """

    def _make_passing_call(self, output_text="Good hint: have you considered this?"):
        """Return a patched __call__ that returns a successful prediction."""

        def patched_call(self_module, **kwargs):
            return dspy.Prediction(response=output_text)

        return patched_call

    def test_bootstrap_selects_examples(self, runner):
        """Bootstrap with always-pass metric selects examples from full_trace."""
        examples = load_training_examples(TRAINING_DATA_PATH)

        def always_pass(example, prediction, trace=None):
            return True

        optimizer = MultiAgentOptimizer(runner)

        with patch.object(
            MultiAgentModule, "__call__", self._make_passing_call()
        ):
            config = optimizer.compile(
                training_examples=examples,
                metric=always_pass,
                optimizer="bootstrap",
                max_bootstrapped_demos=4,
            )

        mgr_examples = config.config.get("manager", {}).get("prompts", {}).get("examples", [])
        # Should have selected some examples (up to max_bootstrapped_demos=4)
        assert len(mgr_examples) > 0
        assert len(mgr_examples) <= len(examples)

    def test_bootstrap_records_provenance(self, runner):
        """After compile, config.optimization.optimized == True, runs list non-empty."""
        examples = load_training_examples(TRAINING_DATA_PATH)

        def always_pass(example, prediction, trace=None):
            return True

        optimizer = MultiAgentOptimizer(runner)

        with patch.object(
            MultiAgentModule, "__call__", self._make_passing_call()
        ):
            config = optimizer.compile(
                training_examples=examples,
                metric=always_pass,
                optimizer="bootstrap",
                max_bootstrapped_demos=2,
            )

        assert config.optimization.optimized is True
        assert len(config.optimization.runs) > 0
        assert config.optimization.runs[-1].optimizer == "bootstrap"

    def test_bootstrap_with_tutor_metric(self, runner):
        """Use tutor_quality_metric from optimize_tutor.py; verify metric passes."""
        from optimize_tutor import tutor_quality_metric

        examples = load_training_examples(TRAINING_DATA_PATH)

        # The hint text must pass tutor_quality_metric: non-trivial, no answer reveal
        hint_text = (
            "Great start! You've correctly identified that momentum involves mass "
            "and velocity. Now think about what units result from multiplying kg by m/s?"
        )

        optimizer = MultiAgentOptimizer(runner)

        with patch.object(
            MultiAgentModule, "__call__", self._make_passing_call(hint_text)
        ):
            config = optimizer.compile(
                training_examples=examples,
                metric=tutor_quality_metric,
                optimizer="bootstrap",
                max_bootstrapped_demos=4,
            )

        # Should have selected examples since metric passes on hint_text
        mgr_examples = config.config.get("manager", {}).get("prompts", {}).get("examples", [])
        assert len(mgr_examples) > 0

    def test_optimization_preserves_worker_structure(self, runner):
        """After optimization, config still has all 3 workers with original prompts."""
        examples = load_training_examples(TRAINING_DATA_PATH)
        original_config = extract_multi_agent_config(runner)

        def always_pass(example, prediction, trace=None):
            return True

        optimizer = MultiAgentOptimizer(runner)

        with patch.object(
            MultiAgentModule, "__call__", self._make_passing_call()
        ):
            config = optimizer.compile(
                training_examples=examples,
                metric=always_pass,
                optimizer="bootstrap",
                max_bootstrapped_demos=2,
            )

        # Workers section preserved
        assert set(config.config["workers"].keys()) == EXPECTED_WORKERS

        # Worker role definitions unchanged
        for name in EXPECTED_WORKERS:
            orig_role = original_config["workers"][name]["prompts"]["role_definition"]
            opt_role = config.config["workers"][name]["prompts"]["role_definition"]
            assert opt_role == orig_role, f"{name} role_definition changed after optimization"
