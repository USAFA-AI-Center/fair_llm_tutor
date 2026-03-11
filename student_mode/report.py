"""Generate sessions/REPORT.md from scored JSONL files.

Reads all .scored.jsonl files in the sessions directory, extracts quality
scores and failure examples, and produces a comprehensive markdown report.

Usage:
    python -m student_mode.report
    python -m student_mode.report --sessions-dir sessions --output sessions/REPORT.md
"""

import argparse
import json
import logging
from collections import defaultdict
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _is_work_turn(record: dict) -> bool:
    si = record.get("student_input", "")
    return (
        not si.startswith(("topic ", "problem "))
        and si not in ("quit", "exit", "q")
        and record.get("tutor_response", "")
    )


def _session_name(path: Path) -> str:
    """Extract a readable session name from filename."""
    return path.stem.replace(".scored", "")


# ── Per-session analysis ──────────────────────────────────────────────────────

def analyze_scored_session(path: Path) -> dict:
    """Analyze a single scored session file and return a summary dict."""
    records = _load_jsonl(path)
    work = [r for r in records if _is_work_turn(r)]
    scored = [r for r in work if "judge_scores" in r]

    if not scored:
        return {"name": _session_name(path), "turns": len(work), "scored_turns": 0}

    dims = ("safety", "pedagogy", "helpfulness", "domain_accuracy")
    avgs = {}
    for dim in dims:
        vals = [r["judge_scores"][dim] for r in scored]
        avgs[dim] = round(sum(vals) / len(vals), 2)
    avgs["overall"] = round(sum(avgs.values()) / len(dims), 2)

    latencies = [r["latency_ms"] for r in work if r.get("latency_ms", 0) > 0]

    # Collect failure turns (any dimension scored 1 or 2)
    failures: list[dict] = []
    for r in scored:
        js = r["judge_scores"]
        failed_dims = [d for d in dims if js[d] <= 2]
        if failed_dims:
            failures.append({
                "turn": r["turn"],
                "student_input": r["student_input"][:120],
                "tutor_response": r["tutor_response"][:200],
                "scores": {d: js[d] for d in dims},
                "failed_dims": failed_dims,
                "reasoning": js.get("reasoning", ""),
            })

    # Collect framework issues
    fw_issues = sum(
        len(r.get("framework_issues", []) or [])
        for r in records
    )

    # Detect problem/topic from setup turns
    topic = ""
    problem = ""
    for r in records:
        si = r.get("student_input", "")
        if si.startswith("topic "):
            topic = si[6:]
        elif si.startswith("problem "):
            problem = si[8:]

    return {
        "name": _session_name(path),
        "topic": topic,
        "problem": problem[:100],
        "turns": len(work),
        "scored_turns": len(scored),
        **avgs,
        "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else 0,
        "max_latency_ms": max(latencies) if latencies else 0,
        "framework_issues": fw_issues,
        "failures": failures,
    }


# ── Domain classification ─────────────────────────────────────────────────────

_DOMAIN_MAP = {
    "calculus": "Math",
    "math": "Math",
    "linear algebra": "Math",
    "statistics": "Math",
    "programming": "Programming",
    "physics": "Science",
    "chemistry": "Science",
    "biology": "Science",
    "history": "Humanities",
    "literature": "Humanities",
    "economics": "Economics / ML",
    "machine learning": "Economics / ML",
}


def _classify_domain(topic: str) -> str:
    return _DOMAIN_MAP.get(topic.lower(), "Other")


# ── Report generation ─────────────────────────────────────────────────────────

def generate_report(sessions: list[dict]) -> str:
    """Generate the full REPORT.md content from session analyses."""
    lines: list[str] = []

    total_turns = sum(s["turns"] for s in sessions)
    all_latencies = [s["avg_latency_ms"] for s in sessions if s["avg_latency_ms"] > 0]
    overall_latency = round(sum(all_latencies) / len(all_latencies)) if all_latencies else 0

    dims = ("safety", "pedagogy", "helpfulness", "domain_accuracy")
    scored_sessions = [s for s in sessions if s.get("scored_turns", 0) > 0]
    dim_means = {}
    for dim in dims:
        vals = [s[dim] for s in scored_sessions if dim in s]
        dim_means[dim] = round(sum(vals) / len(vals), 2) if vals else 0
    overall_mean = round(sum(dim_means.values()) / len(dims), 2)

    today = date.today().isoformat()

    # ── Executive Summary ─────────────────────────────────────────────────
    lines.append("# FAIR-LLM Tutor: Comprehensive Findings Report")
    lines.append("")
    lines.append(f"**Date:** {today}")
    lines.append(f"**Scenarios:** {len(sessions)} across {len(set(_classify_domain(s.get('topic', '')) for s in sessions))} domains")
    lines.append(f"**Total Turns Evaluated:** {total_turns}")
    lines.append("**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(
        f"This report presents findings from a {len(sessions)}-scenario stress test "
        f"of the FAIR-LLM Socratic tutoring system. Sessions were scored by "
        f"`student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, "
        f"and Domain Accuracy."
    )
    lines.append("")
    lines.append(f"**Overall system score: {overall_mean:.2f} / 5.00** (mean across all sessions and dimensions)")
    lines.append(f"**Average latency:** {overall_latency}ms per turn")
    lines.append("")

    # Verdict
    if overall_mean >= 4.0:
        verdict = "The system is approaching readiness for supervised deployment with real students."
    elif overall_mean >= 3.5:
        verdict = "The system shows promise but needs targeted improvements before real student deployment."
    else:
        verdict = "The system needs significant improvements before it can be considered safe for deployment with real students."
    lines.append(verdict)
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Quality Scorecard ─────────────────────────────────────────────────
    lines.append("## Quality Scorecard")
    lines.append("")
    lines.append("| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |")
    lines.append("|---------|--------|----------|-------------|------------|---------|-------|")
    for s in sorted(scored_sessions, key=lambda x: x["name"]):
        overall = s.get("overall", 0)
        marker = "**" if overall < 3.0 or any(s.get(d, 5) < 3.0 for d in dims) else ""
        lines.append(
            f"| {s['name']} "
            f"| {s.get('safety', 0):.2f} "
            f"| {s.get('pedagogy', 0):.2f} "
            f"| {s.get('helpfulness', 0):.2f} "
            f"| {s.get('domain_accuracy', 0):.2f} "
            f"| {marker}{overall:.2f}{marker} "
            f"| {s['turns']} |"
        )
    lines.append(
        f"| **Mean** "
        f"| **{dim_means.get('safety', 0):.2f}** "
        f"| **{dim_means.get('pedagogy', 0):.2f}** "
        f"| **{dim_means.get('helpfulness', 0):.2f}** "
        f"| **{dim_means.get('domain_accuracy', 0):.2f}** "
        f"| **{overall_mean:.2f}** | |"
    )
    lines.append("")

    # Dimension averages
    lines.append("### Dimension Averages")
    lines.append("")
    lines.append("| Dimension | Mean Score |")
    lines.append("|-----------|-----------|")
    for dim in dims:
        lines.append(f"| {dim.replace('_', ' ').title()} | {dim_means.get(dim, 0):.2f} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Strengths ─────────────────────────────────────────────────────────
    lines.append("## Strengths")
    lines.append("")
    top_sessions = sorted(scored_sessions, key=lambda x: x.get("overall", 0), reverse=True)[:3]
    for s in top_sessions:
        lines.append(f"- **{s['name']}** scored {s.get('overall', 0):.2f} overall (topic: {s.get('topic', 'unknown')})")
    lines.append("")

    best_dim = max(dims, key=lambda d: dim_means.get(d, 0))
    lines.append(f"**Strongest dimension:** {best_dim.replace('_', ' ').title()} ({dim_means[best_dim]:.2f})")
    lines.append("")

    fw_zero = [s for s in sessions if s.get("framework_issues", 0) == 0]
    lines.append(f"**Framework stability:** {len(fw_zero)} of {len(sessions)} sessions produced zero framework issues.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Weaknesses & Failure Modes ────────────────────────────────────────
    lines.append("## Weaknesses and Failure Modes")
    lines.append("")

    # Group failures by type
    all_failures: list[dict] = []
    for s in scored_sessions:
        for f in s.get("failures", []):
            f["session"] = s["name"]
            all_failures.append(f)

    failure_groups: dict[str, list[dict]] = defaultdict(list)
    for f in all_failures:
        for dim in f["failed_dims"]:
            failure_groups[dim].append(f)

    dim_labels = {
        "safety": "Answer Revelation / Safety Failures",
        "pedagogy": "Pedagogy Failures",
        "helpfulness": "Helpfulness Failures",
        "domain_accuracy": "Domain Accuracy Failures",
    }

    for dim in dims:
        failures = failure_groups.get(dim, [])
        if not failures:
            continue
        lines.append(f"### {dim_labels[dim]} ({len(failures)} turns)")
        lines.append("")
        # Show up to 5 examples
        for f in failures[:5]:
            lines.append(
                f"- **{f['session']} turn {f['turn']}** (scores: "
                f"S={f['scores']['safety']}, P={f['scores']['pedagogy']}, "
                f"H={f['scores']['helpfulness']}, D={f['scores']['domain_accuracy']})"
            )
            lines.append(f'  - Student: "{f["student_input"]}"')
            lines.append(f'  - Tutor: "{f["tutor_response"]}"')
            if f.get("reasoning"):
                lines.append(f'  - Judge: "{f["reasoning"][:150]}"')
            lines.append("")
        if len(failures) > 5:
            lines.append(f"  ... and {len(failures) - 5} more turns")
            lines.append("")

    lines.append("---")
    lines.append("")

    # ── Domain-by-Domain Breakdown ────────────────────────────────────────
    lines.append("## Domain-by-Domain Breakdown")
    lines.append("")

    by_domain: dict[str, list[dict]] = defaultdict(list)
    for s in scored_sessions:
        domain = _classify_domain(s.get("topic", ""))
        by_domain[domain].append(s)

    for domain in sorted(by_domain.keys()):
        domain_sessions = by_domain[domain]
        domain_overall = round(
            sum(s.get("overall", 0) for s in domain_sessions) / len(domain_sessions), 2
        )
        lines.append(f"### {domain} (avg {domain_overall:.2f})")
        lines.append("")
        lines.append("| Session | Overall | Notes |")
        lines.append("|---------|---------|-------|")
        for s in sorted(domain_sessions, key=lambda x: x.get("overall", 0), reverse=True):
            fw = f"{s.get('framework_issues', 0)} fw issues" if s.get("framework_issues", 0) > 0 else ""
            fail_count = len(s.get("failures", []))
            notes = f"{fail_count} failure turns" if fail_count > 0 else "Clean"
            if fw:
                notes = f"{notes}. {fw}"
            lines.append(f"| {s['name']} | {s.get('overall', 0):.2f} | {notes} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Recommendations ───────────────────────────────────────────────────
    lines.append("## Recommendations")
    lines.append("")

    # Auto-generate recommendations from failure patterns
    safety_count = len(failure_groups.get("safety", []))
    pedagogy_count = len(failure_groups.get("pedagogy", []))
    helpfulness_count = len(failure_groups.get("helpfulness", []))
    accuracy_count = len(failure_groups.get("domain_accuracy", []))
    total_fw = sum(s.get("framework_issues", 0) for s in sessions)

    rec_num = 1
    if safety_count > 0:
        lines.append(f"### P0 — Safety ({safety_count} failure turns)")
        lines.append("")
        lines.append(
            f"**{rec_num}. Fix answer confirmation/revelation behavior.** "
            f"{safety_count} turns scored safety <= 2. The tutor must never confirm "
            f"correct answers without first asking the student to explain their reasoning."
        )
        lines.append("")
        rec_num += 1

    if total_fw > 0:
        lines.append(f"**{rec_num}. Eliminate framework leaks.** "
                     f"{total_fw} framework issues detected across sessions.")
        lines.append("")
        rec_num += 1

    if accuracy_count > 0:
        lines.append(f"### P1 — Correctness ({accuracy_count} failure turns)")
        lines.append("")
        lines.append(
            f"**{rec_num}. Fix domain accuracy issues.** "
            f"{accuracy_count} turns scored domain_accuracy <= 2."
        )
        lines.append("")
        rec_num += 1

    if pedagogy_count > 0:
        lines.append(f"### P2 — Pedagogy ({pedagogy_count} failure turns)")
        lines.append("")
        lines.append(
            f"**{rec_num}. Improve pedagogical quality.** "
            f"{pedagogy_count} turns scored pedagogy <= 2. "
            f"Focus on Socratic questioning over direct instruction."
        )
        lines.append("")
        rec_num += 1

    if helpfulness_count > 0:
        lines.append(
            f"**{rec_num}. Improve helpfulness.** "
            f"{helpfulness_count} turns scored helpfulness <= 2."
        )
        lines.append("")
        rec_num += 1

    lines.append("---")
    lines.append("")

    # ── Raw Statistics ────────────────────────────────────────────────────
    lines.append("## Raw Statistics")
    lines.append("")
    lines.append("### Per-Session Latency")
    lines.append("")
    lines.append("| Session | Avg Latency (ms) | Max Latency (ms) |")
    lines.append("|---------|-----------------:|----------------:|")
    for s in sorted(sessions, key=lambda x: x.get("avg_latency_ms", 0), reverse=True):
        lines.append(
            f"| {s['name']} | {s.get('avg_latency_ms', 0):,} | {s.get('max_latency_ms', 0):,} |"
        )
    lines.append("")
    lines.append(f"**Overall mean latency:** ~{overall_latency:,}ms per turn")
    lines.append("")

    # Issue frequency
    lines.append("### Issue Frequency Summary")
    lines.append("")
    lines.append("| Issue Type | Failure Turns |")
    lines.append("|------------|--------------|")
    for dim in dims:
        count = len(failure_groups.get(dim, []))
        if count > 0:
            lines.append(f"| {dim_labels[dim]} | {count} |")
    if total_fw > 0:
        lines.append(f"| Framework issues | {total_fw} |")
    lines.append("")

    # Score distribution
    lines.append("### Score Distribution")
    lines.append("")
    lines.append("| Score Range | Sessions |")
    lines.append("|-------------|---------|")
    ranges = [(4.0, 5.01, "4.00+"), (3.5, 4.0, "3.50 – 3.99"), (3.0, 3.5, "3.00 – 3.49"), (0, 3.0, "< 3.00")]
    for lo, hi, label in ranges:
        count = sum(1 for s in scored_sessions if lo <= s.get("overall", 0) < hi)
        if count > 0:
            names = ", ".join(s["name"] for s in scored_sessions if lo <= s.get("overall", 0) < hi)
            lines.append(f"| {label} | {count} ({names}) |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        f"*Report auto-generated from {len(sessions)} scored session files on {today}. "
        f"Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*"
    )
    lines.append("")

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate REPORT.md from scored JSONL session files"
    )
    parser.add_argument(
        "--sessions-dir", type=str, default="sessions",
        help="Directory containing .scored.jsonl files (default: sessions)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output path (default: <sessions-dir>/REPORT.md)",
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    sessions_dir = Path(args.sessions_dir)
    scored_files = sorted(sessions_dir.glob("*.scored.jsonl"))

    if not scored_files:
        print(f"No .scored.jsonl files found in {sessions_dir}/")
        return

    print(f"Found {len(scored_files)} scored session files")

    sessions = []
    for path in scored_files:
        analysis = analyze_scored_session(path)
        sessions.append(analysis)
        print(f"  {analysis['name']}: overall={analysis.get('overall', 'N/A')}, "
              f"turns={analysis['turns']}, failures={len(analysis.get('failures', []))}")

    report = generate_report(sessions)

    output_path = Path(args.output) if args.output else sessions_dir / "REPORT.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to {output_path}")
    print(f"Overall score: {sum(s.get('overall', 0) for s in sessions if s.get('scored_turns', 0) > 0) / max(1, sum(1 for s in sessions if s.get('scored_turns', 0) > 0)):.2f} / 5.00")


if __name__ == "__main__":
    main()
