"""Main entry point for the self-improving optimizer loop.

Usage:
    python -m optimizer.loop                          # full run (10 iterations, core5)
    python -m optimizer.loop --baseline-only           # measure baseline only
    python -m optimizer.loop --dry-run --max-iterations 1  # propose but don't apply
    python -m optimizer.loop --max-iterations 3        # 3-iteration run
    python -m optimizer.loop --scenario-set all        # use all 17 scenarios
    python -m optimizer.loop --resume                  # resume from history.json
"""

import argparse
import logging
import sys
from dataclasses import asdict

from optimizer.applier import (
    apply_changes,
    commit_changes,
    create_iteration_branch,
    get_current_branch,
    revert_and_return,
    run_git,
    run_tests,
)
from optimizer.config import OptimizerConfig
from optimizer.proposer import propose_changes
from optimizer.scorer import run_and_score
from optimizer.tracker import IterationRecord, Tracker

logger = logging.getLogger(__name__)


def run_baseline(config: OptimizerConfig, tracker: Tracker) -> float:
    """Phase 0: measure baseline scores on the current branch."""
    print("\n" + "=" * 60)
    print("PHASE 0: BASELINE MEASUREMENT")
    print("=" * 60)

    scores = run_and_score(config, iteration=0)
    tracker.record_baseline(scores)

    print(f"\nBaseline weighted score: {scores.weighted:.3f}")
    print(f"  safety:          {scores.dimensions.safety:.2f}")
    print(f"  pedagogy:        {scores.dimensions.pedagogy:.2f}")
    print(f"  helpfulness:     {scores.dimensions.helpfulness:.2f}")
    print(f"  domain_accuracy: {scores.dimensions.domain_accuracy:.2f}")

    for s in scores.per_scenario:
        print(f"  [{s.scenario}] weighted={s.weighted:.3f}")

    return scores.weighted


def run_iteration(
    config: OptimizerConfig,
    tracker: Tracker,
    iteration: int,
    original_branch: str,
    dry_run: bool = False,
) -> str:
    """Run one optimizer iteration. Returns status string."""
    print(f"\n{'=' * 60}")
    print(f"ITERATION {iteration}")
    print(f"{'=' * 60}")

    _, best_score = tracker.get_best()
    best_branch = tracker.get_best_branch()

    # If a previous iteration improved things, start from that branch
    if best_branch:
        run_git("checkout", best_branch, check=False)

    # ── Step 1: Get current scores for context ──────────────────────
    # Use the best known scores to inform the proposer.
    # Re-read from tracker rather than re-running (baseline or last improved).
    baseline = tracker.get_baseline_score()
    print(f"  Current best: {best_score:.3f} (baseline: {baseline:.3f})")

    # Build scores from the most recent good state for the proposer.
    # We need to run and score the current state if we haven't yet.
    current_scores = run_and_score(config, iteration=iteration)

    # ── Step 2: Propose changes ─────────────────────────────────────
    print("  Proposing changes...")
    proposal = propose_changes(config, current_scores, tracker)

    if proposal.hypothesis == "PARSE_FAILURE":
        print("  ERROR: Failed to parse proposal from Claude")
        record = IterationRecord(
            iteration=iteration,
            scores=current_scores,
            hypothesis="PARSE_FAILURE",
            branch="",
            status="apply_failed",
        )
        tracker.record_iteration(record)
        if best_branch:
            revert_and_return(best_branch)
        else:
            revert_and_return(original_branch)
        return "apply_failed"

    if not proposal.changes:
        print("  No changes proposed")
        record = IterationRecord(
            iteration=iteration,
            scores=current_scores,
            hypothesis=proposal.hypothesis,
            branch="",
            status="apply_failed",
            changes=[],
        )
        tracker.record_iteration(record)
        if best_branch:
            revert_and_return(best_branch)
        else:
            revert_and_return(original_branch)
        return "apply_failed"

    print(f"  Hypothesis: {proposal.hypothesis}")
    print(f"  Changes: {len(proposal.changes)} across {len({c.file_path for c in proposal.changes})} file(s)")
    for c in proposal.changes:
        print(f"    {c.file_path}: {c.rationale[:80]}")

    if dry_run:
        print("  [DRY RUN] Skipping apply/test/score")
        record = IterationRecord(
            iteration=iteration,
            scores=current_scores,
            hypothesis=proposal.hypothesis,
            branch="",
            status="dry_run",
            changes=[asdict(c) for c in proposal.changes],
        )
        tracker.record_iteration(record)
        return "dry_run"

    # ── Step 3: Create branch and apply changes ─────────────────────
    # Go back to the best branch before creating the iteration branch
    if best_branch:
        run_git("checkout", best_branch, check=False)
    else:
        run_git("checkout", original_branch, check=False)

    branch = create_iteration_branch(iteration)
    success, errors = apply_changes(proposal)

    if not success:
        print(f"  APPLY FAILED: {'; '.join(errors)}")
        record = IterationRecord(
            iteration=iteration,
            scores=current_scores,
            hypothesis=proposal.hypothesis,
            branch=branch,
            status="apply_failed",
            changes=[asdict(c) for c in proposal.changes],
        )
        tracker.record_iteration(record)
        revert_and_return(best_branch or original_branch)
        return "apply_failed"

    # ── Step 4: Run tests ───────────────────────────────────────────
    print("  Running tests...")
    tests_passed, test_output = run_tests()

    if not tests_passed:
        print("  TESTS FAILED")
        # Still commit so the branch is preserved for review
        commit_changes(proposal, iteration)
        record = IterationRecord(
            iteration=iteration,
            scores=current_scores,
            hypothesis=proposal.hypothesis,
            branch=branch,
            status="tests_failed",
            changes=[asdict(c) for c in proposal.changes],
        )
        tracker.record_iteration(record)
        revert_and_return(best_branch or original_branch)
        return "tests_failed"

    # Commit passing changes
    commit_changes(proposal, iteration)

    # ── Step 5: Re-score with changes applied ───────────────────────
    print("  Scoring with changes applied...")
    new_scores = run_and_score(config, iteration=iteration)

    # ── Step 6: Accept or reject ────────────────────────────────────
    delta = new_scores.weighted - best_score
    print(f"  Score delta: {delta:+.3f} ({best_score:.3f} -> {new_scores.weighted:.3f})")

    if delta >= -config.plateau_threshold:  # improved or within noise
        status = "improved"
        print(f"  ACCEPTED (delta={delta:+.3f})")
    else:
        status = "regressed"
        print(f"  REJECTED (regression of {delta:.3f})")

    record = IterationRecord(
        iteration=iteration,
        scores=new_scores,
        hypothesis=proposal.hypothesis,
        branch=branch,
        status=status,
        changes=[asdict(c) for c in proposal.changes],
    )
    tracker.record_iteration(record)

    if status == "regressed":
        # Branch is preserved for review, but revert to previous best
        revert_and_return(best_branch or original_branch)

    return status


def main():
    parser = argparse.ArgumentParser(
        description="Self-improving optimizer loop for fair_llm_tutor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--max-iterations", type=int, default=None,
                        help="Override max iterations (default: from config)")
    parser.add_argument("--scenario-set", choices=["core5", "all"], default=None,
                        help="Scenario set (default: core5)")
    parser.add_argument("--optimizer-model", type=str, default=None,
                        help="Claude model for proposals")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing history.json")
    parser.add_argument("--baseline-only", action="store_true",
                        help="Only measure baseline, no iterations")
    parser.add_argument("--dry-run", action="store_true",
                        help="Propose changes but don't apply them")
    parser.add_argument("--weights", type=str, default=None,
                        help="Custom weights as 'safety,pedagogy,helpfulness,accuracy' (e.g. '0.4,0.2,0.2,0.2')")
    parser.add_argument("--log-level", type=str, default="INFO")

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # Build config
    config = OptimizerConfig()
    if args.max_iterations is not None:
        config.max_iterations = args.max_iterations
    if args.scenario_set is not None:
        config.scenario_set = args.scenario_set
    if args.optimizer_model is not None:
        config.optimizer_model = args.optimizer_model
    if args.weights:
        parts = [float(x) for x in args.weights.split(",")]
        if len(parts) == 4:
            config.weight_safety = parts[0]
            config.weight_pedagogy = parts[1]
            config.weight_helpfulness = parts[2]
            config.weight_domain_accuracy = parts[3]

    tracker = Tracker(config)
    original_branch = get_current_branch()

    print("=" * 60)
    print("FAIR-LLM TUTOR OPTIMIZER")
    print("=" * 60)
    print(f"  Scenario set:    {config.scenario_set} ({len(config.get_scenario_names())} scenarios)")
    print(f"  Max iterations:  {config.max_iterations}")
    print(f"  Optimizer model: {config.optimizer_model}")
    print(f"  Judge:           {config.judge_provider}/{config.judge_model}")
    print(f"  Weights:         {config.weights}")
    print(f"  Branch:          {original_branch}")
    print(f"  Dry run:         {args.dry_run}")

    # ── Phase 0: Baseline ───────────────────────────────────────────
    if args.resume and tracker.get_baseline_score() is not None:
        print(f"\nResuming from existing baseline: {tracker.get_baseline_score():.3f}")
        start_iteration = tracker.get_iteration_count() + 1
    else:
        run_baseline(config, tracker)
        start_iteration = 1

    if args.baseline_only:
        print("\n--baseline-only: stopping after baseline measurement")
        return

    # ── Phase 1-N: Iteration loop ───────────────────────────────────
    for iteration in range(start_iteration, start_iteration + config.max_iterations):
        # Check stop conditions
        _, best_score = tracker.get_best()
        if best_score >= config.near_perfect_score:
            print(f"\nNear-perfect score ({best_score:.3f} >= {config.near_perfect_score}). Stopping.")
            break

        if tracker.is_plateaued():
            print(f"\nPlateau detected (last {config.plateau_patience} iterations within "
                  f"{config.plateau_threshold}). Stopping.")
            break

        status = run_iteration(config, tracker, iteration, original_branch, dry_run=args.dry_run)
        print(f"  Iteration {iteration} result: {status}")

    # ── Final summary ───────────────────────────────────────────────
    best_iter, best_score = tracker.get_best()
    best_branch = tracker.get_best_branch()
    baseline = tracker.get_baseline_score()

    print(f"\n{'=' * 60}")
    print("OPTIMIZER COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Baseline score:  {baseline:.3f}")
    print(f"  Best score:      {best_score:.3f}")
    if best_iter is not None:
        print(f"  Best iteration:  {best_iter}")
        print(f"  Best branch:     {best_branch}")
        print(f"  Review command:  git diff {original_branch}..{best_branch}")
    else:
        print("  No improvement over baseline")
    print(f"  History:         {config.tracker_path}")
    print(f"  Runs:            {config.runs_dir}/")

    # Return to original branch
    run_git("checkout", original_branch, check=False)


if __name__ == "__main__":
    main()
