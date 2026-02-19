"""Tests for config.py — TutorConfig."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TutorConfig


class TestTutorConfigDefaults:
    """Tests for default configuration values."""

    def test_default_model_name(self):
        config = TutorConfig()
        assert config.model_name == "Qwen/Qwen2.5-14B-Instruct"

    def test_default_max_new_tokens(self):
        config = TutorConfig()
        assert config.max_new_tokens == 1000

    def test_default_manager_max_steps(self):
        config = TutorConfig()
        assert config.manager_max_steps == 15

    def test_default_rag_top_k(self):
        config = TutorConfig()
        assert config.rag_top_k == 3

    def test_default_chromadb_persist_path_is_none(self):
        config = TutorConfig()
        assert config.chromadb_persist_path is None


class TestTutorConfigValidation:
    """Tests for config validation."""

    def test_valid_config_no_warnings(self):
        config = TutorConfig()
        warnings = config.validate()
        assert len(warnings) == 0

    def test_empty_model_name_warning(self):
        config = TutorConfig(model_name="")
        warnings = config.validate()
        assert any("model_name" in w for w in warnings)

    def test_negative_max_new_tokens_warning(self):
        config = TutorConfig(max_new_tokens=0)
        warnings = config.validate()
        assert any("max_new_tokens" in w for w in warnings)

    def test_negative_rag_top_k_warning(self):
        config = TutorConfig(rag_top_k=0)
        warnings = config.validate()
        assert any("rag_top_k" in w for w in warnings)

    def test_negative_manager_max_steps_warning(self):
        config = TutorConfig(manager_max_steps=-1)
        warnings = config.validate()
        assert any("manager_max_steps" in w for w in warnings)


class TestTutorConfigFromEnv:
    """Tests for environment variable loading."""

    def test_env_overrides_model_name(self, monkeypatch):
        monkeypatch.setenv("FAIR_LLM_MODEL_NAME", "test-model")
        config = TutorConfig.from_env()
        assert config.model_name == "test-model"

    def test_env_overrides_max_new_tokens(self, monkeypatch):
        monkeypatch.setenv("FAIR_LLM_MAX_NEW_TOKENS", "2000")
        config = TutorConfig.from_env()
        assert config.max_new_tokens == 2000

    def test_env_overrides_auth_token(self, monkeypatch):
        monkeypatch.setenv("FAIR_LLM_AUTH_TOKEN", "my-secret-token")
        config = TutorConfig.from_env()
        assert config.auth_token == "my-secret-token"

    def test_env_overrides_rag_top_k(self, monkeypatch):
        monkeypatch.setenv("FAIR_LLM_RAG_TOP_K", "5")
        config = TutorConfig.from_env()
        assert config.rag_top_k == 5

    def test_invalid_env_var_ignored(self, monkeypatch):
        monkeypatch.setenv("FAIR_LLM_MAX_NEW_TOKENS", "not_a_number")
        config = TutorConfig.from_env()
        # Should fall back to default
        assert config.max_new_tokens == 1000

    def test_no_env_vars_uses_defaults(self):
        # Ensure none of our env vars are set
        for key in list(os.environ.keys()):
            if key.startswith("FAIR_LLM_"):
                del os.environ[key]

        config = TutorConfig.from_env()
        assert config.model_name == "Qwen/Qwen2.5-14B-Instruct"


class TestTutorConfigCustomValues:
    """Tests for custom instantiation."""

    def test_custom_values(self):
        config = TutorConfig(
            model_name="custom-model",
            max_new_tokens=500,
            manager_max_steps=20,
            rag_top_k=5,
            chromadb_persist_path="/tmp/test_chroma"
        )
        assert config.model_name == "custom-model"
        assert config.max_new_tokens == 500
        assert config.manager_max_steps == 20
        assert config.rag_top_k == 5
        assert config.chromadb_persist_path == "/tmp/test_chroma"
