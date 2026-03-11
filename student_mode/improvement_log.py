"""Generate IMPROVEMENT_LOG.md: the bridge between two pipeline runs.

Connects old failures → code changes → new results, giving the next
improvement cycle full context about what was tried and what worked.

This file is written into each run directory (alongside REPORT.md and
COMPARISON.md) whenever a previous run exists to compare against.

The log answers three questions:
  1. What was wrong? (previous run's failures and recommendations)
  2. What changed? (code diff between runs)
  3. Did it work? (score deltas, new/resolved failures)
"""

import json
from pathlib import Path


def _read_report_sections(run_dir: Path) -> dict[str, str]:
    """Extract key sections from a run's REPORT.md."""
    report_path = run_dir / "REPORT.md"
    if not report_path.exists():
        return {}

    text = report_path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current_heading = ""
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def _extract_failures(manifest: dict) -> list[dict]:
    """Extract per-session failure info from a manifest."""
    per_session = manifest.get("scores", {}).get("per_session", {})
    dims = ("safety", "pedagogy", "helpfulness", "domain_accuracy")
    failures = []
    for name, scores in per_session.items():
        weak = [d for d in dims if scores.get(d, 5) <= 2.5]
        if weak:
            failures.append({"session": name, "overall": scores.get("overall", 0), "weak_dims": weak})
    return failures


def generate_improvement_log(
    old_run_dir: Path,
    new_run_dir: Path,
    old_manifest: dict,
    new_manifest: dict,
) -> str:
    """Generate the improvement log connecting two runs.

    Args:
        old_run_dir: Previous run directory (has REPORT.md).
        new_run_dir: Current run directory (has REPORT.md).
        old_manifest: Previous run's manifest dict.
        new_manifest: Current run's manifest dict.

    Returns:
        Markdown string for IMPROVEMENT_LOG.md.
    """
    lines: list[str] = []
    dims = ("safety", "pedagogy", "helpfulness", "domain_accuracy")

    old_scores = old_manifest.get("scores", {})
    new_scores = new_manifest.get("scores", {})
    old_overall = old_scores.get("overall", 0)
    new_overall = new_scores.get("overall", 0)
    delta = new_overall - old_overall

    # ── Header ────────────────────────────────────────────────────────────
    lines.append("# Improvement Log")
    lines.append("")
    lines.append(f"**Baseline run:** `{old_manifest['run_id']}`")
    lines.append(f"**Current run:** `{new_manifest['run_id']}`")
    lines.append(f"**Score change:** {old_overall:.2f} → {new_overall:.2f} ({delta:+.2f})")
    lines.append("")

    # Attribution
    attr = new_manifest.get("code_attribution", "")
    if attr:
        lines.append(f"> {attr}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Section 1: What was wrong ─────────────────────────────────────────
    lines.append("## 1. What Was Wrong (Baseline Findings)")
    lines.append("")
    lines.append(
        f"The baseline run scored **{old_overall:.2f}/5.00**. "
        f"Below are the issues identified in that run."
    )
    lines.append("")

    # Pull recommendations from old report
    old_sections = _read_report_sections(old_run_dir)
    old_recommendations = old_sections.get("Recommendations", "")
    if old_recommendations:
        lines.append("### Recommendations from Baseline Report")
        lines.append("")
        lines.append(old_recommendations)
        lines.append("")
    else:
        lines.append("*(No recommendations section found in baseline REPORT.md)*")
        lines.append("")

    # Pull weaknesses from old report
    old_weaknesses = old_sections.get("Weaknesses & Failure Modes", "")
    if old_weaknesses:
        lines.append("### Failure Modes from Baseline")
        lines.append("")
        # Truncate if very long — keep first ~60 lines
        weak_lines = old_weaknesses.splitlines()
        if len(weak_lines) > 60:
            lines.extend(weak_lines[:60])
            lines.append(f"*(... {len(weak_lines) - 60} more lines — see baseline REPORT.md)*")
        else:
            lines.append(old_weaknesses)
        lines.append("")

    # Baseline per-session weak spots
    old_failures = _extract_failures(old_manifest)
    if old_failures:
        lines.append("### Weakest Sessions (Baseline)")
        lines.append("")
        lines.append("| Session | Overall | Weak Dimensions |")
        lines.append("|---------|---------|-----------------|")
        for f in sorted(old_failures, key=lambda x: x["overall"]):
            dims_str = ", ".join(d.replace("_", " ") for d in f["weak_dims"])
            lines.append(f"| {f['session']} | {f['overall']:.2f} | {dims_str} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Section 2: What changed ───────────────────────────────────────────
    lines.append("## 2. What Changed (Code Modifications)")
    lines.append("")

    new_git = new_manifest.get("git", {})
    old_git = old_manifest.get("git", {})

    old_commit = old_git.get("commit", "unknown")[:8]
    new_commit = new_git.get("commit", "unknown")[:8]

    if old_commit != new_commit:
        lines.append(f"Git moved from `{old_commit}` to `{new_commit}`.")
    else:
        lines.append(f"Same base commit: `{new_commit}`.")
    lines.append("")

    # Show uncommitted changes (the actual code modifications)
    diff_summary = new_git.get("diff_summary", [])
    diff_stat = new_git.get("diff_stat", "")
    if diff_summary:
        lines.append("### Uncommitted Changes That Produced Current Scores")
        lines.append("")
        lines.append("```")
        for line in diff_summary:
            lines.append(line)
        stat_lines = diff_stat.strip().splitlines()
        if stat_lines and "changed" in stat_lines[-1]:
            lines.append(stat_lines[-1].strip())
        lines.append("```")
        lines.append("")
    elif new_git.get("dirty"):
        dirty_files = new_git.get("dirty_files", [])
        if dirty_files:
            lines.append("### Modified Files")
            lines.append("")
            for f in dirty_files:
                lines.append(f"- `{f}`")
            lines.append("")
    else:
        lines.append("No uncommitted changes — scores produced by committed code.")
        lines.append("")

    # Show which tracked files changed (by checksum)
    old_checksums = old_manifest.get("file_checksums", {})
    new_checksums = new_manifest.get("file_checksums", {})
    changed_files = [
        f for f in sorted(set(old_checksums) | set(new_checksums))
        if old_checksums.get(f) != new_checksums.get(f)
    ]
    if changed_files:
        lines.append("### Tracked Files With Content Changes")
        lines.append("")
        lines.append(
            "These are the tutor source files that differ between baseline "
            "and current. Changes here are the most likely cause of score differences."
        )
        lines.append("")
        for f in changed_files:
            lines.append(f"- **`{f}`**")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Section 3: Did it work? ───────────────────────────────────────────
    lines.append("## 3. Results (Did It Work?)")
    lines.append("")

    # Overall verdict
    if delta > 0.1:
        verdict = "IMPROVED"
    elif delta < -0.1:
        verdict = "REGRESSED"
    else:
        verdict = "NO SIGNIFICANT CHANGE"
    lines.append(f"**Verdict: {verdict}** ({old_overall:.2f} → {new_overall:.2f}, {delta:+.2f})")
    lines.append("")

    # Per-dimension deltas
    lines.append("### Per-Dimension Changes")
    lines.append("")
    lines.append("| Dimension | Baseline | Current | Delta |")
    lines.append("|-----------|----------|---------|-------|")
    old_dims = old_scores.get("dimensions", {})
    new_dims = new_scores.get("dimensions", {})
    for dim in dims:
        ov = old_dims.get(dim, 0)
        nv = new_dims.get(dim, 0)
        d = nv - ov
        sign = "+" if d > 0 else ""
        label = dim.replace("_", " ").title()
        marker = ""
        if d > 0.2:
            marker = " IMPROVED"
        elif d < -0.2:
            marker = " REGRESSED"
        lines.append(f"| {label} | {ov:.2f} | {nv:.2f} | {sign}{d:.2f}{marker} |")
    lines.append("")

    # Per-session comparison (biggest movers)
    old_per_session = old_scores.get("per_session", {})
    new_per_session = new_scores.get("per_session", {})
    all_names = sorted(set(old_per_session) | set(new_per_session))

    if all_names:
        session_deltas = []
        for name in all_names:
            ov = old_per_session.get(name, {}).get("overall", 0)
            nv = new_per_session.get(name, {}).get("overall", 0)
            session_deltas.append((name, ov, nv, nv - ov))

        # Show biggest movers
        session_deltas.sort(key=lambda x: abs(x[3]), reverse=True)

        lines.append("### Session Changes (by magnitude)")
        lines.append("")
        lines.append("| Session | Baseline | Current | Delta |")
        lines.append("|---------|----------|---------|-------|")
        for name, ov, nv, d in session_deltas:
            sign = "+" if d > 0 else ""
            lines.append(f"| {name} | {ov:.2f} | {nv:.2f} | {sign}{d:.2f} |")
        lines.append("")

    # New failures (in current but not in baseline)
    new_failures = _extract_failures(new_manifest)
    old_failure_names = {f["session"] for f in _extract_failures(old_manifest)}
    new_failure_names = {f["session"] for f in new_failures}

    resolved = old_failure_names - new_failure_names
    introduced = new_failure_names - old_failure_names
    persistent = old_failure_names & new_failure_names

    if resolved:
        lines.append("### Resolved Failures")
        lines.append("")
        for name in sorted(resolved):
            lines.append(f"- {name} — no longer has weak dimensions")
        lines.append("")

    if introduced:
        lines.append("### New Failures (Regressions)")
        lines.append("")
        for name in sorted(introduced):
            f = next(f for f in new_failures if f["session"] == name)
            dims_str = ", ".join(d.replace("_", " ") for d in f["weak_dims"])
            lines.append(f"- **{name}** — new weak dims: {dims_str}")
        lines.append("")

    if persistent:
        lines.append("### Persistent Failures (Not Yet Fixed)")
        lines.append("")
        for name in sorted(persistent):
            lines.append(f"- {name}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Section 4: What to do next ────────────────────────────────────────
    lines.append("## 4. Recommendations for Next Cycle")
    lines.append("")

    # Pull recommendations from new report
    new_sections = _read_report_sections(new_run_dir)
    new_recommendations = new_sections.get("Recommendations", "")
    if new_recommendations:
        lines.append(new_recommendations)
    else:
        lines.append("*(See current REPORT.md for detailed recommendations)*")
    lines.append("")

    # Summary of what still needs attention
    remaining_count = new_manifest.get("total_failure_turns", 0)
    old_count = old_manifest.get("total_failure_turns", 0)
    lines.append(
        f"**Failure turns:** {old_count} → {remaining_count} "
        f"({remaining_count - old_count:+d})"
    )
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        f"*Generated by `student_mode.improvement_log` comparing "
        f"`{old_manifest['run_id']}` → `{new_manifest['run_id']}`.*"
    )
    lines.append("")

    return "\n".join(lines)
