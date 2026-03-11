"""Compare two pipeline runs and show score deltas.

Reads ``run_manifest.json`` from two run directories and displays:
  - Overall score change
  - Per-dimension changes
  - Per-session changes (sorted by largest regression first)
  - Files that changed between runs

Usage:
    python -m student_mode.compare sessions/run_20260311_1930 sessions/run_20260311_2045
    python -m student_mode.compare --latest          # compare two most recent runs
    python -m student_mode.compare --latest 3        # compare run N-2 vs latest
"""

import argparse
import json
import sys
from pathlib import Path


def _load_manifest(run_dir: Path) -> dict:
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: No run_manifest.json in {run_dir}")
        sys.exit(1)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _delta_str(old: float, new: float) -> str:
    """Format a delta with color-like markers."""
    diff = new - old
    if abs(diff) < 0.005:
        return f"{new:.2f}  (=)"
    sign = "+" if diff > 0 else ""
    marker = "^" if diff > 0 else "v"
    return f"{new:.2f}  ({sign}{diff:.2f} {marker})"


def compare_runs(old: dict, new: dict) -> str:
    """Generate a comparison report between two manifests."""
    lines: list[str] = []

    lines.append("# Run Comparison")
    lines.append("")
    lines.append(f"**Baseline:** {old['run_id']}  ({old['timestamp'][:19]})")
    lines.append(f"**Current:**  {new['run_id']}  ({new['timestamp'][:19]})")
    lines.append("")

    # Code attribution — what code produced each run's scores?
    old_attr = old.get("code_attribution", "")
    new_attr = new.get("code_attribution", "")
    if new_attr:
        lines.append(f"**Current run:** {new_attr}")
    if old_attr:
        lines.append(f"**Baseline run:** {old_attr}")
    lines.append("")

    # Git info
    old_git = old.get("git", {})
    new_git = new.get("git", {})
    old_commit = old_git.get("commit", "unknown")[:8]
    new_commit = new_git.get("commit", "unknown")[:8]
    if old_commit != new_commit:
        lines.append(f"**Git:** `{old_commit}` → `{new_commit}`")
    else:
        lines.append(f"**Git:** `{new_commit}` (same commit)")
        if new_git.get("dirty"):
            lines.append("  (working tree has uncommitted changes)")
    lines.append("")

    # Show what uncommitted changes produced the current scores
    new_diff_summary = new_git.get("diff_summary", [])
    if new_diff_summary:
        lines.append("### Uncommitted Changes (current run)")
        lines.append("")
        lines.append("These code changes produced the current scores:")
        lines.append("")
        lines.append("```")
        for line in new_diff_summary:
            lines.append(line)
        diff_stat = new_git.get("diff_stat", "")
        # Last line of diff --stat is the summary (e.g. "5 files changed, 120 insertions...")
        stat_lines = diff_stat.strip().splitlines()
        if stat_lines and "changed" in stat_lines[-1]:
            lines.append(stat_lines[-1].strip())
        lines.append("```")
        lines.append("")

    # Overall score
    old_overall = old["scores"]["overall"]
    new_overall = new["scores"]["overall"]
    diff = new_overall - old_overall
    direction = "IMPROVED" if diff > 0 else "REGRESSED" if diff < 0 else "UNCHANGED"
    lines.append(f"## Overall: {old_overall:.2f} → {new_overall:.2f}  ({direction}, {diff:+.2f})")
    lines.append("")

    # Dimension breakdown
    lines.append("## Per-Dimension")
    lines.append("")
    lines.append("| Dimension | Baseline | Current | Delta |")
    lines.append("|-----------|----------|---------|-------|")
    old_dims = old["scores"].get("dimensions", {})
    new_dims = new["scores"].get("dimensions", {})
    for dim in ("safety", "pedagogy", "helpfulness", "domain_accuracy"):
        ov = old_dims.get(dim, 0)
        nv = new_dims.get(dim, 0)
        d = nv - ov
        sign = "+" if d > 0 else ""
        label = dim.replace("_", " ").title()
        lines.append(f"| {label} | {ov:.2f} | {nv:.2f} | {sign}{d:.2f} |")
    lines.append("")

    # Per-session breakdown
    old_sessions = old["scores"].get("per_session", {})
    new_sessions = new["scores"].get("per_session", {})
    all_names = sorted(set(old_sessions) | set(new_sessions))

    if all_names:
        lines.append("## Per-Session")
        lines.append("")
        lines.append("| Session | Baseline | Current | Delta |")
        lines.append("|---------|----------|---------|-------|")

        deltas = []
        for name in all_names:
            ov = old_sessions.get(name, {}).get("overall", 0)
            nv = new_sessions.get(name, {}).get("overall", 0)
            deltas.append((name, ov, nv, nv - ov))

        # Sort: regressions first, then improvements
        deltas.sort(key=lambda x: x[3])

        for name, ov, nv, d in deltas:
            sign = "+" if d > 0 else ""
            marker = ""
            if d < -0.2:
                marker = " REGRESSED"
            elif d > 0.2:
                marker = " IMPROVED"
            lines.append(f"| {name} | {ov:.2f} | {nv:.2f} | {sign}{d:.2f}{marker} |")
        lines.append("")

    # Changed files
    old_checksums = old.get("file_checksums", {})
    new_checksums = new.get("file_checksums", {})
    changed = [
        f for f in sorted(set(old_checksums) | set(new_checksums))
        if old_checksums.get(f) != new_checksums.get(f)
    ]
    if changed:
        lines.append("## Changed Files")
        lines.append("")
        for f in changed:
            old_hash = old_checksums.get(f, "missing")[:8]
            new_hash = new_checksums.get(f, "missing")[:8]
            lines.append(f"- `{f}`: `{old_hash}` → `{new_hash}`")
        lines.append("")
    else:
        lines.append("## Changed Files")
        lines.append("")
        lines.append("No tracked files changed between runs.")
        lines.append("")

    # Failure count
    old_fails = old.get("total_failure_turns", 0)
    new_fails = new.get("total_failure_turns", 0)
    fail_diff = new_fails - old_fails
    sign = "+" if fail_diff > 0 else ""
    lines.append(f"**Failure turns:** {old_fails} → {new_fails} ({sign}{fail_diff})")
    lines.append("")

    return "\n".join(lines)


def find_runs(sessions_dir: Path) -> list[Path]:
    """Find all run directories, sorted by name (oldest first)."""
    return sorted(
        d for d in sessions_dir.iterdir()
        if d.is_dir() and d.name.startswith("run_") and (d / "run_manifest.json").exists()
    )


def main():
    parser = argparse.ArgumentParser(
        description="Compare two pipeline runs and show score deltas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m student_mode.compare sessions/run_A sessions/run_B
  python -m student_mode.compare --latest
  python -m student_mode.compare --latest 3   # compare 3rd-latest vs latest
        """,
    )
    parser.add_argument("runs", nargs="*", help="Two run directories to compare")
    parser.add_argument(
        "--latest", nargs="?", const=2, type=int, default=None,
        help="Compare Nth-latest run vs latest (default: 2 = previous vs latest)",
    )
    parser.add_argument(
        "--sessions-dir", type=str, default="sessions",
        help="Parent directory containing run_* directories",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write comparison to file instead of stdout",
    )

    args = parser.parse_args()

    if args.latest is not None:
        runs = find_runs(Path(args.sessions_dir))
        if len(runs) < 2:
            print(f"Need at least 2 runs to compare. Found {len(runs)}.")
            sys.exit(1)
        idx = min(args.latest, len(runs))
        old_dir = runs[-idx]
        new_dir = runs[-1]
    elif len(args.runs) == 2:
        old_dir = Path(args.runs[0])
        new_dir = Path(args.runs[1])
    else:
        parser.error("Provide two run directories, or use --latest")
        return

    print(f"Comparing: {old_dir.name} → {new_dir.name}")

    old_manifest = _load_manifest(old_dir)
    new_manifest = _load_manifest(new_dir)

    report = compare_runs(old_manifest, new_manifest)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Comparison written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
