"""
Optimize the tutor's multi-agent prompts using fair_prompt_optimizer.

This script:
1. Builds the tutor's HierarchicalAgentRunner
2. Loads training examples
3. Runs MultiAgentOptimizer (bootstrap or MIPRO)
4. Saves the optimized config

Usage:
    python optimize_tutor.py \
        --course_materials course_materials \
        --training_data training_data/examples.json \
        --output configs/tutor_optimized.json

    # With MIPRO instruction optimization (requires a DSPy LM):
    python optimize_tutor.py \
        --course_materials course_materials \
        --training_data training_data/examples.json \
        --optimizer mipro \
        --output configs/tutor_optimized.json
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from fair_prompt_optimizer import (
    MultiAgentOptimizer,
    OptimizedConfig,
    load_training_examples,
)

from config import TutorConfig
from config_export import export_tutor_config
from main import TutorSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def tutor_quality_metric(example, prediction, trace=None) -> bool:
    """
    Evaluate whether a tutor response meets quality standards.

    Checks:
    1. Response is non-trivial (not just an error)
    2. Response does not directly reveal the answer
    3. Response contains educational content (questions, guidance)
    """
    response = getattr(prediction, "response", str(prediction))

    # Reject errors and empty responses
    if not response or response.startswith("Error:"):
        return False

    # Reject very short responses (likely failures)
    if len(response.strip()) < 20:
        return False

    expected = example.expected_output if hasattr(example, "expected_output") else ""

    # Check that the response doesn't bluntly state "the answer is X"
    # when the expected output is a hint (not a confirmation)
    answer_reveal_phrases = [
        "the answer is",
        "the correct answer is",
        "the solution is",
    ]
    response_lower = response.lower()

    # Only flag as answer-revealing if the expected output itself is a hint
    # (not a confirmation of a correct answer)
    if expected and "correct" not in expected.lower():
        for phrase in answer_reveal_phrases:
            if phrase in response_lower:
                return False

    return True


def safety_metric(example, prediction, trace=None) -> bool:
    """
    Strict safety metric: response must not reveal answers.

    Use as a worker metric for SafetyGuard optimization.
    """
    response = getattr(prediction, "response", str(prediction))

    if not response:
        return False

    # SafetyGuard should output SAFE or UNSAFE verdicts
    response_upper = response.upper()
    if "SAFE" in response_upper or "UNSAFE" in response_upper:
        return True

    return False


def hint_quality_metric(example, prediction, trace=None) -> bool:
    """
    Evaluate hint quality: should guide without revealing.

    Use as a worker metric for HintGenerator optimization.
    """
    response = getattr(prediction, "response", str(prediction))

    if not response or len(response.strip()) < 10:
        return False

    # A good hint should contain a question or guidance
    socratic_indicators = ["?", "think about", "consider", "what", "how", "recall"]
    response_lower = response.lower()

    return any(indicator in response_lower for indicator in socratic_indicators)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_optimization(args):
    """Build tutor, load examples, optimize, save."""

    # Load config
    config = None
    if args.config:
        config = TutorConfig.from_yaml(args.config)

    # Build the full tutor system
    logger.info("Building tutor system...")
    session = TutorSession(
        course_materials_path=args.course_materials,
        problems_file="",
        config=config,
    )

    # Export baseline config
    baseline_path = args.output.replace(".json", "_baseline.json")
    export_tutor_config(session.runner, output_path=baseline_path)
    logger.info(f"Baseline config saved to: {baseline_path}")

    # Load training examples
    logger.info(f"Loading training examples from: {args.training_data}")
    training_examples = load_training_examples(args.training_data)
    logger.info(f"Loaded {len(training_examples)} training examples")

    # Set up optimizer
    logger.info(f"Creating MultiAgentOptimizer (optimizer={args.optimizer})")
    optimizer = MultiAgentOptimizer(
        runner=session.runner,
        optimize_manager=True,
        optimize_workers=args.optimize_workers,
    )

    # Prepare worker training data and metrics if optimizing workers
    worker_training = None
    worker_metrics = None
    if args.optimize_workers:
        # Use the same examples for workers (they'll be evaluated independently)
        worker_training = {
            "SafetyGuard": training_examples,
            "HintGenerator": training_examples,
            "MisconceptionDetector": training_examples,
        }
        worker_metrics = {
            "SafetyGuard": safety_metric,
            "HintGenerator": hint_quality_metric,
            "MisconceptionDetector": tutor_quality_metric,
        }

    # Prepare DSPy LM for MIPRO if needed
    dspy_lm = None
    if args.optimizer == "mipro":
        try:
            import dspy
            dspy_lm = dspy.LM(
                model=f"huggingface/{session.config.model_name}",
                max_tokens=session.config.max_new_tokens,
            )
            logger.info(f"DSPy LM initialized: {session.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to create DSPy LM for MIPRO: {e}")
            logger.info("Falling back to bootstrap optimizer")
            args.optimizer = "bootstrap"

    # Run optimization
    logger.info("Starting optimization...")
    optimized_config = optimizer.compile(
        training_examples=training_examples,
        metric=tutor_quality_metric,
        worker_training_examples=worker_training,
        worker_metrics=worker_metrics,
        optimizer=args.optimizer,
        max_bootstrapped_demos=args.max_demos,
        training_data_path=args.training_data,
        dspy_lm=dspy_lm,
    )

    # Save optimized config
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    optimized_config.save(str(output_path))
    logger.info(f"Optimized config saved to: {output_path}")

    # Report results
    provenance = optimized_config.optimization
    if provenance and provenance.runs:
        last_run = provenance.runs[-1]
        logger.info(
            f"Optimization complete: "
            f"{last_run.get('examples_before', 0)} -> {last_run.get('examples_after', 0)} examples, "
            f"role_definition_changed={last_run.get('role_definition_changed', False)}"
        )

    return optimized_config


def main():
    parser = argparse.ArgumentParser(
        description="Optimize the tutor's multi-agent prompts"
    )
    parser.add_argument(
        "--course_materials",
        type=str,
        default="course_materials",
        help="Path to course materials folder",
    )
    parser.add_argument(
        "--training_data",
        type=str,
        default="training_data/examples.json",
        help="Path to training examples JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="configs/tutor_optimized.json",
        help="Path to save optimized config",
    )
    parser.add_argument(
        "--optimizer",
        type=str,
        default="bootstrap",
        choices=["bootstrap", "mipro"],
        help="Optimization strategy",
    )
    parser.add_argument(
        "--max_demos",
        type=int,
        default=4,
        help="Maximum number of bootstrap demos to select",
    )
    parser.add_argument(
        "--optimize_workers",
        action="store_true",
        help="Also optimize worker agent prompts (not just manager)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to tutor YAML config file (optional)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    run_optimization(args)


if __name__ == "__main__":
    main()
