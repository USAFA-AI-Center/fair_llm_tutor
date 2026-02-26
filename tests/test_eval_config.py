"""Tests for eval configuration."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.eval_config import EvalConfig


class TestEvalConfig:
    def test_default_config(self):
        config = EvalConfig()
        assert config.tutor_model is not None
        assert config.judge_model is not None
        assert config.student_model is not None

    def test_custom_models(self):
        config = EvalConfig(
            tutor_model="gpt-4",
            judge_model="claude-3-opus",
            student_model="gpt-3.5-turbo",
        )
        assert config.tutor_model == "gpt-4"

    def test_num_conversations_default(self):
        config = EvalConfig()
        assert config.num_conversations > 0

    def test_from_dict(self):
        d = {"tutor_model": "test-model", "num_conversations": 10}
        config = EvalConfig(**d)
        assert config.tutor_model == "test-model"
        assert config.num_conversations == 10

    def test_default_paths(self):
        config = EvalConfig()
        assert config.scenarios_path == "eval/scenarios.json"
        assert config.output_path == "eval/results.json"

    def test_max_turns_default(self):
        config = EvalConfig()
        assert config.max_turns_per_conversation == 5
