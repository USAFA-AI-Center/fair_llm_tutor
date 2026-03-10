# config.py

"""
Tutor configuration module.

Supports loading from:
- Direct instantiation: TutorConfig(model_name="...")
- Environment variables: FAIR_LLM_MODEL_NAME, FAIR_LLM_AUTH_TOKEN, etc.
- YAML file: TutorConfig.from_yaml("config.yaml")
"""

import dataclasses
import os
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def _parse_bool(v: str) -> bool:
    return v.lower() in ("true", "1", "yes")


@dataclass
class TutorConfig:
    """Configuration for the FAIR_LLM Tutor system."""

    # Model settings (HuggingFace only)
    model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    max_new_tokens: int = 400
    quantized: bool = False
    auth_token: str = ""

    # Agent step limit
    max_steps: int = 10

    # Safety settings
    max_input_length: int = 2000

    # Pedagogical settings
    escalation_threshold: int = 3

    # LLM generation settings
    stream: bool = False
    verbose: bool = False

    # RAG settings
    collection_name: str = "course_materials"
    chromadb_persist_path: Optional[str] = None
    rag_top_k: int = 3

    @classmethod
    def from_env(cls) -> "TutorConfig":
        """Load config with environment variable overrides."""
        config = cls()

        env_map: dict[str, tuple[str, Callable[[str], Any]]] = {
            "FAIR_LLM_MODEL_NAME": ("model_name", str),
            "FAIR_LLM_MAX_NEW_TOKENS": ("max_new_tokens", int),
            "FAIR_LLM_QUANTIZED": ("quantized", _parse_bool),
            "FAIR_LLM_AUTH_TOKEN": ("auth_token", str),
            "FAIR_LLM_MAX_STEPS": ("max_steps", int),
            "FAIR_LLM_MAX_INPUT_LENGTH": ("max_input_length", int),
            "FAIR_LLM_ESCALATION_THRESHOLD": ("escalation_threshold", int),
            "FAIR_LLM_STREAM": ("stream", _parse_bool),
            "FAIR_LLM_VERBOSE": ("verbose", _parse_bool),
            "FAIR_LLM_COLLECTION_NAME": ("collection_name", str),
            "FAIR_LLM_CHROMADB_PERSIST_PATH": ("chromadb_persist_path", str),
            "FAIR_LLM_RAG_TOP_K": ("rag_top_k", int),
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

        field_names = {f.name for f in dataclasses.fields(cls)}
        config = cls(**{k: v for k, v in data.items() if k in field_names})

        # Apply env overrides on top
        env_config = cls.from_env()
        for env_var in os.environ:
            if env_var.startswith("FAIR_LLM_"):
                attr = env_var.replace("FAIR_LLM_", "").lower()
                if hasattr(config, attr):
                    setattr(config, attr, getattr(env_config, attr))

        return config

    def validate(self) -> list[str]:
        """Validate config and return list of warnings."""
        warnings = []

        if not self.model_name:
            warnings.append("model_name is empty")
        if self.max_new_tokens < 1:
            warnings.append(f"max_new_tokens must be positive, got {self.max_new_tokens}")
        if self.rag_top_k < 1:
            warnings.append(f"rag_top_k must be positive, got {self.rag_top_k}")
        if self.max_steps < 1:
            warnings.append(f"max_steps must be positive, got {self.max_steps}")

        for w in warnings:
            logger.warning(f"Config validation: {w}")

        return warnings
