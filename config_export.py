"""
Export tutor multi-agent configuration for use with fair_prompt_optimizer.

This module bridges fair_llm_tutor and fair_prompt_optimizer by extracting
the tutor's HierarchicalAgentRunner configuration into an OptimizedConfig
that the MultiAgentOptimizer can consume.

Usage:
    from config_export import export_tutor_config
    config = export_tutor_config(tutor_session.runner)
    config.save("configs/tutor_baseline.json")
"""

import logging
from typing import Optional

from fairlib.utils.config_manager import extract_multi_agent_config
from fair_prompt_optimizer import OptimizedConfig

logger = logging.getLogger(__name__)


def export_tutor_config(
    runner: "HierarchicalAgentRunner",
    output_path: Optional[str] = None,
) -> OptimizedConfig:
    """
    Export the tutor's multi-agent runner config for optimization.

    Extracts prompts, examples, and structure from the running
    HierarchicalAgentRunner and wraps them in an OptimizedConfig
    compatible with MultiAgentOptimizer.

    Args:
        runner: The tutor's HierarchicalAgentRunner instance
        output_path: Optional path to save the config JSON

    Returns:
        OptimizedConfig ready for MultiAgentOptimizer
    """
    logger.info("Extracting multi-agent config from tutor runner...")

    config_dict = extract_multi_agent_config(runner)
    config = OptimizedConfig(config=config_dict)

    logger.info(
        f"Exported config: manager + {len(config_dict.get('workers', {}))} workers "
        f"({', '.join(config_dict.get('workers', {}).keys())})"
    )

    if output_path:
        config.save(output_path)
        logger.info(f"Saved baseline config to: {output_path}")

    return config
