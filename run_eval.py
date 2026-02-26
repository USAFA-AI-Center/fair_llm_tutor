"""CLI entry point for running tutor evaluations.

Usage:
    source .venv/bin/activate
    python run_eval.py --scenarios eval/scenarios.json --num-conversations 10

Requires a running LLM (local or API) and course materials for RAG.
"""

import argparse
import asyncio
import json
import logging
import sys

from eval.eval_config import EvalConfig
from eval.eval_harness import EvalHarness
from eval.scenarios import load_scenarios

logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(
        description="Run automated tutor evaluation with simulated students"
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        default="eval/scenarios.json",
        help="Path to scenarios JSON file",
    )
    parser.add_argument(
        "--num-conversations",
        type=int,
        default=None,
        help="Number of scenarios to run (default: all)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=5,
        help="Max turns per conversation (default: 5)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval/results.json",
        help="Path to write results JSON",
    )
    parser.add_argument(
        "--course-materials",
        type=str,
        default="course_materials",
        help="Path to course materials folder",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (default: from TutorConfig)",
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default=None,
        help="Judge model name (default: same as tutor model)",
    )
    parser.add_argument(
        "--student-model",
        type=str,
        default=None,
        help="Simulated student model name (default: same as tutor model)",
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

    # Build config
    config = EvalConfig(
        scenarios_path=args.scenarios,
        max_turns_per_conversation=args.max_turns,
        output_path=args.output,
        course_materials_path=args.course_materials,
    )
    if args.model:
        config.tutor_model = args.model
    if args.judge_model:
        config.judge_model = args.judge_model
    if args.student_model:
        config.student_model = args.student_model

    # Load scenarios
    scenarios = load_scenarios(config.scenarios_path)
    if args.num_conversations:
        scenarios = scenarios[: args.num_conversations]

    logger.info(f"Loaded {len(scenarios)} scenarios from {config.scenarios_path}")

    # Build tutor session
    # Import here to avoid loading heavy dependencies until needed
    from main import TutorSession

    logger.info("Initializing tutor session...")
    session = TutorSession(
        course_materials_path=config.course_materials_path,
    )

    # Build LLMs for student and judge
    # By default, reuse the tutor's LLM; override if different models specified
    student_llm = session.llm
    judge_llm = session.llm

    if config.student_model != config.tutor_model:
        from fairlib import HuggingFaceAdapter
        student_llm = HuggingFaceAdapter(model_name=config.student_model)

    if config.judge_model != config.tutor_model:
        from fairlib import HuggingFaceAdapter
        judge_llm = HuggingFaceAdapter(model_name=config.judge_model)

    # Build and run harness
    harness = EvalHarness(
        config=config,
        tutor_fn=session.process_student_work,
        student_llm=student_llm,
        judge_llm=judge_llm,
    )

    logger.info("Starting evaluation...")
    report = await harness.run(scenarios)

    # Write results
    with open(config.output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)

    # Print summary
    agg = report.aggregate()
    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Scenarios run: {len(report.results)}")
    print(f"Safety:          {agg['safety']:.2f}/5.0")
    print(f"Pedagogy:        {agg['pedagogy']:.2f}/5.0")
    print(f"Helpfulness:     {agg['helpfulness']:.2f}/5.0")
    print(f"Domain Accuracy: {agg['domain_accuracy']:.2f}/5.0")
    print(f"\nFull results saved to: {config.output_path}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
