"""Run scenarios and score them with the LLM-as-judge.

Integrates ``student_mode.runner.run_session`` and
``student_mode.judge.score_session`` into a single scoring pipeline
that returns an ``IterationScore``.
"""

import json
import logging
from pathlib import Path

from optimizer.config import OptimizerConfig
from optimizer.tracker import DimensionScores, IterationScore, ScenarioScore
from student_mode.judge import SessionJudge, score_session
from student_mode.scenarios import get_scenario

logger = logging.getLogger(__name__)


def _build_judge(config: OptimizerConfig) -> SessionJudge:
    """Build a SessionJudge from config."""
    from student_mode.judge import _build_llm
    llm = _build_llm(config.judge_provider, config.judge_model)
    return SessionJudge(llm)


def _compute_weighted(dims: DimensionScores, weights: dict[str, float]) -> float:
    return (
        dims.safety * weights["safety"]
        + dims.pedagogy * weights["pedagogy"]
        + dims.helpfulness * weights["helpfulness"]
        + dims.domain_accuracy * weights["domain_accuracy"]
    )


def run_and_score(config: OptimizerConfig, iteration: int) -> IterationScore:
    """Run all configured scenarios and return aggregated scores.

    For each scenario:
      1. Run a deterministic student session via ``run_session()``.
      2. Score the JSONL output with the LLM judge.
      3. Aggregate per-dimension averages.

    Args:
        config: Optimizer configuration.
        iteration: Iteration number (-1 for baseline).

    Returns:
        IterationScore with per-scenario breakdown and weighted aggregate.
    """
    from student_mode.runner import run_session

    scenario_names = config.get_scenario_names()
    run_dir = Path(config.runs_dir) / f"iter_{iteration:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    judge = _build_judge(config)
    weights = config.weights
    scenario_scores: list[ScenarioScore] = []

    for name in scenario_names:
        scenario = get_scenario(name)
        output_path = str(run_dir / f"{name}.jsonl")

        logger.info("Running scenario %s (iteration %d)", name, iteration)
        try:
            summary = run_session(
                topic=scenario.topic,
                problem=scenario.problem,
                initial_work=scenario.initial_work,
                module=scenario.module,
                correct_answer=scenario.correct_answer or None,
                output_path=output_path,
                max_turns=config.max_turns,
                min_turns=config.min_turns,
                timeout=config.session_timeout,
                log_level="WARNING",
            )
        except Exception as e:
            logger.error("Scenario %s failed during session: %s", name, e)
            scenario_scores.append(ScenarioScore(
                scenario=name,
                dimensions=DimensionScores(
                    safety=1.0, pedagogy=1.0,
                    helpfulness=1.0, domain_accuracy=1.0,
                ),
                weighted=1.0,
                turn_count=0,
                judge_reasoning=[f"Session failed: {e}"],
            ))
            continue

        # Score the session
        logger.info("Scoring scenario %s", name)
        try:
            scored_records = score_session(
                judge=judge,
                jsonl_path=output_path,
                correct_answer=scenario.correct_answer or None,
                expected_behavior=scenario.expected_behavior,
            )
        except Exception as e:
            logger.error("Scenario %s failed during scoring: %s", name, e)
            scenario_scores.append(ScenarioScore(
                scenario=name,
                dimensions=DimensionScores(
                    safety=1.0, pedagogy=1.0,
                    helpfulness=1.0, domain_accuracy=1.0,
                ),
                weighted=1.0,
                turn_count=summary.get("work_turns", 0),
                judge_reasoning=[f"Scoring failed: {e}"],
            ))
            continue

        # Extract scores from work turns
        work_records = [r for r in scored_records if "judge_scores" in r]
        if not work_records:
            scenario_scores.append(ScenarioScore(
                scenario=name,
                dimensions=DimensionScores(
                    safety=1.0, pedagogy=1.0,
                    helpfulness=1.0, domain_accuracy=1.0,
                ),
                weighted=1.0,
                turn_count=0,
                judge_reasoning=["No work turns scored"],
            ))
            continue

        n = len(work_records)
        dims = DimensionScores(
            safety=sum(r["judge_scores"]["safety"] for r in work_records) / n,
            pedagogy=sum(r["judge_scores"]["pedagogy"] for r in work_records) / n,
            helpfulness=sum(r["judge_scores"]["helpfulness"] for r in work_records) / n,
            domain_accuracy=sum(r["judge_scores"]["domain_accuracy"] for r in work_records) / n,
        )

        reasoning = [r["judge_scores"].get("reasoning", "") for r in work_records]

        scenario_scores.append(ScenarioScore(
            scenario=name,
            dimensions=dims,
            weighted=_compute_weighted(dims, weights),
            turn_count=n,
            judge_reasoning=reasoning,
        ))

    # Aggregate across scenarios
    if scenario_scores:
        n_scenarios = len(scenario_scores)
        agg_dims = DimensionScores(
            safety=sum(s.dimensions.safety for s in scenario_scores) / n_scenarios,
            pedagogy=sum(s.dimensions.pedagogy for s in scenario_scores) / n_scenarios,
            helpfulness=sum(s.dimensions.helpfulness for s in scenario_scores) / n_scenarios,
            domain_accuracy=sum(s.dimensions.domain_accuracy for s in scenario_scores) / n_scenarios,
        )
    else:
        agg_dims = DimensionScores(safety=1.0, pedagogy=1.0, helpfulness=1.0, domain_accuracy=1.0)

    result = IterationScore(
        iteration=iteration,
        per_scenario=scenario_scores,
        dimensions=agg_dims,
        weighted=_compute_weighted(agg_dims, weights),
    )

    # Write summary
    summary_path = run_dir / "summary.json"
    from dataclasses import asdict
    with open(summary_path, "w") as f:
        json.dump(asdict(result), f, indent=2)

    logger.info(
        "Iteration %d scored: weighted=%.3f (safety=%.2f pedagogy=%.2f help=%.2f accuracy=%.2f)",
        iteration, result.weighted,
        agg_dims.safety, agg_dims.pedagogy,
        agg_dims.helpfulness, agg_dims.domain_accuracy,
    )

    return result
