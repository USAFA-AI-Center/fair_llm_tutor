# config.py

"""
Tutor configuration module.

Supports loading from:
- Direct instantiation: TutorConfig(model_name="...")
- Environment variables: FAIR_LLM_MODEL_NAME, FAIR_LLM_AUTH_TOKEN, etc.
- YAML file: TutorConfig.from_yaml("config.yaml")
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TutorConfig:
    """Configuration for the FAIR_LLM Tutor system."""

    # Model settings (HuggingFace only)
    model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    max_new_tokens: int = 1000
    quantized: bool = False
    auth_token: str = ""

    # Agent step limits
    manager_max_steps: int = 15
    safety_max_steps: int = 5
    misconception_max_steps: int = 10
    hint_max_steps: int = 10

    # RAG settings
    collection_name: str = "course_materials"
    chromadb_persist_path: Optional[str] = None
    rag_top_k: int = 3

    # Runner settings
    runner_max_steps: int = 15

    @classmethod
    def from_env(cls) -> "TutorConfig":
        """Load config with environment variable overrides."""
        config = cls()

        env_map = {
            "FAIR_LLM_MODEL_NAME": ("model_name", str),
            "FAIR_LLM_MAX_NEW_TOKENS": ("max_new_tokens", int),
            "FAIR_LLM_QUANTIZED": ("quantized", lambda v: v.lower() in ("true", "1", "yes")),
            "FAIR_LLM_AUTH_TOKEN": ("auth_token", str),
            "FAIR_LLM_MANAGER_MAX_STEPS": ("manager_max_steps", int),
            "FAIR_LLM_SAFETY_MAX_STEPS": ("safety_max_steps", int),
            "FAIR_LLM_MISCONCEPTION_MAX_STEPS": ("misconception_max_steps", int),
            "FAIR_LLM_HINT_MAX_STEPS": ("hint_max_steps", int),
            "FAIR_LLM_COLLECTION_NAME": ("collection_name", str),
            "FAIR_LLM_CHROMADB_PERSIST_PATH": ("chromadb_persist_path", str),
            "FAIR_LLM_RAG_TOP_K": ("rag_top_k", int),
            "FAIR_LLM_RUNNER_MAX_STEPS": ("runner_max_steps", int),
        }

        for env_var, (attr, converter) in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    setattr(config, attr, converter(value))
                    logger.debug(f"Config override from env: {env_var}={value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid env var {env_var}={value}: {e}")

        return config

    @classmethod
    def from_yaml(cls, path: str) -> "TutorConfig":
        """Load config from YAML file with env overrides on top."""
        import yaml

        filepath = Path(path)
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(filepath, "r") as f:
            data = yaml.safe_load(f) or {}

        config = cls(**{k: v for k, v in data.items() if hasattr(cls, k)})

        # Apply env overrides on top
        env_config = cls.from_env()
        for env_var in os.environ:
            if env_var.startswith("FAIR_LLM_"):
                attr = env_var.replace("FAIR_LLM_", "").lower()
                if hasattr(config, attr):
                    setattr(config, attr, getattr(env_config, attr))

        return config

    def validate(self) -> list:
        """Validate config and return list of warnings."""
        warnings = []

        if not self.model_name:
            warnings.append("model_name is empty")
        if self.max_new_tokens < 1:
            warnings.append(f"max_new_tokens must be positive, got {self.max_new_tokens}")
        if self.rag_top_k < 1:
            warnings.append(f"rag_top_k must be positive, got {self.rag_top_k}")
        if self.manager_max_steps < 1:
            warnings.append(f"manager_max_steps must be positive, got {self.manager_max_steps}")

        for w in warnings:
            logger.warning(f"Config validation: {w}")

        return warnings
