"""End-to-end pipeline: run sessions → judge → report → compare.

Single command that replaces multi-step agent orchestration.
Each run writes to a timestamped directory (``sessions/run_<timestamp>/``)
with a ``run_manifest.json`` that captures code state and scores.

Usage:
    python -m student_mode.pipeline                          # full pipeline
    python -m student_mode.pipeline --skip-sessions          # judge + report only
    python -m student_mode.pipeline --skip-sessions --skip-judge  # report only
    python -m student_mode.pipeline --scenario derivatives   # single scenario
"""

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from student_mode.scenarios import SCENARIOS, scenario_names

logger = logging.getLogger(__name__)


def _run_cmd(cmd: list[str], description: str, timeout: int = 600) -> bool:
    """Run a subprocess and return True on success."""
    print(f"\n{'─' * 60}")
    print(f"  {description}")
    print(f"  $ {' '.join(cmd)}")
    print(f"{'─' * 60}")

    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=False,
        )
        if result.returncode != 0:
            print(f"  WARNING: exited with code {result.returncode}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  ERROR: timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def _create_run_dir(base_dir: str) -> Path:
    """Create a timestamped run directory."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(base_dir) / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _find_previous_run(base_dir: str, current_run: Path) -> Path | None:
    """Find the most recent run directory before *current_run*."""
    from student_mode.compare import find_runs
    runs = find_runs(Path(base_dir))
    # Filter out the current run
    previous = [r for r in runs if r != current_run]
    return previous[-1] if previous else None


def run_sessions(
    scenarios: list[str] | None = None,
    student_llm: str = "anthropic",
    max_turns: int = 15,
    timeout: int = 300,
    output_dir: str = "sessions",
) -> list[Path]:
    """Phase 1: Run student sessions."""
    print("\n" + "=" * 60)
    print("  PHASE 1: RUN SESSIONS")
    print("=" * 60)

    if scenarios is None:
        # Run all
        cmd = [
            sys.executable, "-m", "student_mode.runner",
            "--all",
            "--student-llm", student_llm,
            "--max-turns", str(max_turns),
            "--timeout", str(timeout),
            "--output-dir", output_dir,
        ]
        _run_cmd(cmd, f"Running all {len(SCENARIOS)} scenarios", timeout=timeout * len(SCENARIOS))
    else:
        for name in scenarios:
            cmd = [
                sys.executable, "-m", "student_mode.runner",
                "--scenario", name,
                "--student-llm", student_llm,
                "--max-turns", str(max_turns),
                "--timeout", str(timeout),
                "--output", str(Path(output_dir) / f"{SCENARIOS[name].module}.jsonl"),
            ]
            _run_cmd(cmd, f"Running scenario: {name}", timeout=timeout * 2)

    # Return list of produced JSONL files
    output_path = Path(output_dir)
    return sorted(output_path.glob("lesson_*.jsonl"))


def run_judge(
    jsonl_files: list[Path],
    llm_provider: str = "anthropic",
    rate_limit_delay: float = 3.0,
) -> list[Path]:
    """Phase 2a: Score each session with LLM-as-judge.

    Runs sequentially with a delay between sessions to respect API rate limits.
    Skips files that already have a newer .scored.jsonl.
    """
    print("\n" + "=" * 60)
    print("  PHASE 2a: JUDGE SCORING")
    print("=" * 60)

    scored_files = []
    for jsonl_path in jsonl_files:
        scored_path = jsonl_path.with_suffix(".scored.jsonl")

        # Skip if scored file exists and is newer
        if scored_path.exists() and scored_path.stat().st_mtime > jsonl_path.stat().st_mtime:
            print(f"  SKIP (up to date): {jsonl_path.name}")
            scored_files.append(scored_path)
            continue

        cmd = [
            sys.executable, "-m", "student_mode.judge",
            str(jsonl_path),
            "--llm", llm_provider,
        ]
        success = _run_cmd(cmd, f"Scoring: {jsonl_path.name}", timeout=600)
        if success and scored_path.exists():
            scored_files.append(scored_path)

        # Rate limit delay between judge calls
        if rate_limit_delay > 0:
            time.sleep(rate_limit_delay)

    return scored_files


def run_report(sessions_dir: str = "sessions") -> Path:
    """Phase 2b: Generate REPORT.md from scored files."""
    print("\n" + "=" * 60)
    print("  PHASE 2b: GENERATE REPORT")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "student_mode.report",
        "--sessions-dir", sessions_dir,
    ]
    _run_cmd(cmd, "Generating REPORT.md")
    return Path(sessions_dir) / "REPORT.md"


def run_aggregate(sessions_dir: str = "sessions") -> None:
    """Run aggregate results display."""
    cmd = [
        sys.executable, "-m", "student_mode.aggregate_results",
        "--sessions-dir", sessions_dir,
    ]
    _run_cmd(cmd, "Aggregate results summary")


def run_manifest_and_compare(
    run_dir: Path,
    base_dir: str,
    session_scores: list[dict],
) -> None:
    """Write manifest, compare with previous run, and generate improvement log."""
    from student_mode.manifest import create_manifest
    from student_mode.compare import compare_runs
    from student_mode.improvement_log import generate_improvement_log

    print("\n" + "=" * 60)
    print("  MANIFEST & COMPARISON")
    print("=" * 60)

    manifest_path = create_manifest(run_dir, session_scores)
    print(f"  Manifest written: {manifest_path}")

    # Find previous run to compare against
    previous = _find_previous_run(base_dir, run_dir)
    if previous:
        print(f"  Comparing with previous run: {previous.name}")
        import json
        old_manifest = json.loads((previous / "run_manifest.json").read_text(encoding="utf-8"))
        new_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        # Write COMPARISON.md (score deltas)
        comparison = compare_runs(old_manifest, new_manifest)
        comp_path = run_dir / "COMPARISON.md"
        comp_path.write_text(comparison, encoding="utf-8")
        print(f"  Comparison written: {comp_path}")

        # Write IMPROVEMENT_LOG.md (full narrative: old failures → code changes → results)
        improvement_log = generate_improvement_log(
            old_run_dir=previous,
            new_run_dir=run_dir,
            old_manifest=old_manifest,
            new_manifest=new_manifest,
        )
        log_path = run_dir / "IMPROVEMENT_LOG.md"
        log_path.write_text(improvement_log, encoding="utf-8")
        print(f"  Improvement log written: {log_path}")

        print()
        print(comparison)
    else:
        print("  No previous run found — this is the first run. Skipping comparison.")


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end pipeline: run sessions → judge → report → compare",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m student_mode.pipeline                          # full pipeline, all scenarios
  python -m student_mode.pipeline --scenario derivatives   # single scenario
  python -m student_mode.pipeline --skip-sessions          # re-judge + re-report existing sessions
  python -m student_mode.pipeline --skip-sessions --skip-judge  # regenerate report only
        """,
    )

    parser.add_argument(
        "--scenario", type=str, choices=scenario_names(),
        action="append", default=None,
        help="Run specific scenario(s). Omit for all. Can be repeated.",
    )
    parser.add_argument("--skip-sessions", action="store_true", help="Skip Phase 1 (session running)")
    parser.add_argument("--skip-judge", action="store_true", help="Skip Phase 2a (judge scoring)")
    parser.add_argument("--skip-report", action="store_true", help="Skip Phase 2b (report generation)")
    parser.add_argument("--student-llm", type=str, default="anthropic", choices=["openai", "anthropic", "ollama"])
    parser.add_argument("--judge-llm", type=str, default="anthropic", choices=["openai", "anthropic", "ollama"])
    parser.add_argument("--max-turns", type=int, default=15)
    parser.add_argument("--timeout", type=int, default=300, help="Per-session timeout in seconds")
    parser.add_argument("--output-dir", type=str, default="sessions")
    parser.add_argument("--rate-limit-delay", type=float, default=3.0, help="Seconds between judge calls")
    parser.add_argument("--log-level", type=str, default="INFO")

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    start = time.monotonic()
    base_dir = args.output_dir
    Path(base_dir).mkdir(exist_ok=True)

    # Create timestamped run directory
    run_dir = _create_run_dir(base_dir)
    print(f"\n  Run directory: {run_dir}")

    # Phase 1: Run sessions (into run directory)
    run_output_dir = str(run_dir)
    if not args.skip_sessions:
        jsonl_files = run_sessions(
            scenarios=args.scenario,
            student_llm=args.student_llm,
            max_turns=args.max_turns,
            timeout=args.timeout,
            output_dir=run_output_dir,
        )
    else:
        # When skipping sessions, look for JSONL in the most recent run dir
        # or in the base sessions dir
        jsonl_files = sorted(run_dir.glob("lesson_*.jsonl"))
        if not jsonl_files:
            # Fall back to base dir (legacy flat layout)
            jsonl_files = sorted(Path(base_dir).glob("lesson_*.jsonl"))
            if jsonl_files:
                # Copy references — judge will write scored files next to originals
                run_output_dir = base_dir
        print(f"\nSkipping sessions. Found {len(jsonl_files)} existing JSONL files.")

    if not jsonl_files:
        print("ERROR: No session files found. Cannot proceed.")
        sys.exit(1)

    # Phase 2a: Judge scoring
    if not args.skip_judge:
        scored_files = run_judge(
            jsonl_files,
            llm_provider=args.judge_llm,
            rate_limit_delay=args.rate_limit_delay,
        )
    else:
        scored_files = sorted(Path(run_output_dir).glob("*.scored.jsonl"))
        print(f"\nSkipping judge. Found {len(scored_files)} existing scored files.")

    # Aggregate display
    run_aggregate(run_output_dir)

    # Phase 2b: Generate report
    if not args.skip_report:
        report_path = run_report(run_output_dir)
    else:
        report_path = Path(run_output_dir) / "REPORT.md"
        print("\nSkipping report generation.")

    # Analyze sessions for manifest
    from student_mode.report import analyze_scored_session
    session_scores = []
    for sf in scored_files:
        session_scores.append(analyze_scored_session(sf))

    # Write manifest and compare with previous run
    run_manifest_and_compare(run_dir, base_dir, session_scores)

    elapsed = time.monotonic() - start
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Run:      {run_dir}")
    print(f"  Sessions: {len(jsonl_files)}")
    print(f"  Scored:   {len(scored_files)}")
    print(f"  Report:   {report_path}")
    print(f"  Elapsed:  {elapsed / 60:.1f} minutes")
    print("=" * 60)


if __name__ == "__main__":
    main()
