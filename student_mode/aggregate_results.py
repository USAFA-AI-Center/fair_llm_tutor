"""
Aggregate and display results from student simulation sessions.

Reads JSONL files from the sessions directory and produces summaries.

Usage:
    python -m student_mode.aggregate_results
    python -m student_mode.aggregate_results --sessions-dir sessions
    python -m student_mode.aggregate_results --session sessions/session_20260227_*.jsonl
"""

import argparse
import json
import glob
from pathlib import Path
from collections import defaultdict


def load_session(path: str) -> list[dict]:
    """Load all records from a JSONL file."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def analyze_session(records: list[dict]) -> dict:
    """Analyze a single session's records."""
    work_records = [
        r for r in records
        if not r["student_input"].startswith(("topic ", "problem "))
        and r["student_input"] not in ("quit", "exit", "q")
    ]

    latencies = [r["latency_ms"] for r in work_records if r["latency_ms"] > 0]
    avg_latency = sum(latencies) // len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0

    # Extract metadata from records
    session_id = records[0]["session_id"] if records else "unknown"
    module = records[0].get("module", "") if records else ""
    topic_record = next((r for r in records if r["student_input"].startswith("topic ")), None)
    topic = topic_record["student_input"].replace("topic ", "") if topic_record else "unknown"
    problem_record = next((r for r in records if r["student_input"].startswith("problem ")), None)
    problem = problem_record["student_input"].replace("problem ", "") if problem_record else "unknown"

    # Check response quality indicators
    empty_responses = sum(1 for r in work_records if not r["tutor_response"])
    has_quality_scores = any(r.get("quality_score") is not None for r in work_records)

    # Calculate response lengths
    response_lengths = [len(r["tutor_response"]) for r in work_records if r["tutor_response"]]
    avg_response_len = sum(response_lengths) // len(response_lengths) if response_lengths else 0

    return {
        "session_id": session_id,
        "module": module,
        "topic": topic,
        "problem": problem[:80],
        "total_turns": len(records),
        "work_turns": len(work_records),
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "total_latency_ms": sum(latencies),
        "empty_responses": empty_responses,
        "avg_response_length": avg_response_len,
        "has_quality_scores": has_quality_scores,
    }


def print_session_detail(records: list[dict], path: str) -> None:
    """Print detailed view of a single session."""
    analysis = analyze_session(records)

    print(f"\n{'=' * 70}")
    print(f"  Session: {analysis['session_id']}  |  File: {path}")
    print(f"  Topic: {analysis['topic']}  |  Module: {analysis['module']}")
    print(f"  Problem: {analysis['problem']}")
    print(f"{'=' * 70}")
    print(f"  Work turns: {analysis['work_turns']}  |  Avg latency: {analysis['avg_latency_ms']}ms  |  Max: {analysis['max_latency_ms']}ms")
    print(f"  Avg response length: {analysis['avg_response_length']} chars  |  Empty responses: {analysis['empty_responses']}")
    print(f"{'=' * 70}")

    work_records = [
        r for r in records
        if not r["student_input"].startswith(("topic ", "problem "))
        and r["student_input"] not in ("quit", "exit", "q")
    ]

    for i, r in enumerate(work_records, 1):
        print(f"\n  Turn {i} ({r['latency_ms']}ms):")
        print(f"    Student: {r['student_input']}")
        tutor_preview = r['tutor_response'][:200] + "..." if len(r['tutor_response']) > 200 else r['tutor_response']
        print(f"    Tutor:   {tutor_preview}")
        if r.get("quality_score") is not None:
            print(f"    Quality: {r['quality_score']}")

    print()


def print_aggregate_summary(sessions: list[dict]) -> None:
    """Print aggregate summary across all sessions."""
    if not sessions:
        print("No sessions found.")
        return

    total_turns = sum(s["work_turns"] for s in sessions)
    total_latency = sum(s["total_latency_ms"] for s in sessions)
    avg_latency = total_latency // total_turns if total_turns else 0
    total_empty = sum(s["empty_responses"] for s in sessions)
    all_latencies_avg = [s["avg_latency_ms"] for s in sessions if s["avg_latency_ms"] > 0]

    print(f"\n{'#' * 70}")
    print(f"  AGGREGATE SUMMARY — {len(sessions)} sessions")
    print(f"{'#' * 70}")
    print(f"  Total work turns:    {total_turns}")
    print(f"  Avg latency/turn:    {avg_latency}ms")
    print(f"  Fastest session avg: {min(all_latencies_avg)}ms" if all_latencies_avg else "")
    print(f"  Slowest session avg: {max(all_latencies_avg)}ms" if all_latencies_avg else "")
    print(f"  Empty responses:     {total_empty}")
    print()

    # Per-session table
    print(f"  {'Session ID':<14} {'Topic':<16} {'Turns':>5} {'Avg ms':>8} {'Max ms':>8} {'Empty':>5}  Module")
    print(f"  {'-' * 14} {'-' * 16} {'-' * 5} {'-' * 8} {'-' * 8} {'-' * 5}  {'-' * 20}")
    for s in sessions:
        print(
            f"  {s['session_id']:<14} {s['topic']:<16} {s['work_turns']:>5} "
            f"{s['avg_latency_ms']:>8} {s['max_latency_ms']:>8} {s['empty_responses']:>5}  {s['module']}"
        )

    # Group by topic
    by_topic = defaultdict(list)
    for s in sessions:
        by_topic[s["topic"]].append(s)

    if len(by_topic) > 1:
        print(f"\n  By topic:")
        for topic, topic_sessions in sorted(by_topic.items()):
            topic_turns = sum(s["work_turns"] for s in topic_sessions)
            topic_latency = sum(s["total_latency_ms"] for s in topic_sessions)
            topic_avg = topic_latency // topic_turns if topic_turns else 0
            print(f"    {topic:<20} {len(topic_sessions)} sessions, {topic_turns} turns, avg {topic_avg}ms")

    print(f"\n{'#' * 70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate and display student simulation session results"
    )
    parser.add_argument(
        "--sessions-dir", type=str, default="sessions",
        help="Directory containing JSONL session files (default: sessions)",
    )
    parser.add_argument(
        "--session", type=str, nargs="*",
        help="Specific JSONL file(s) to analyze (supports globs)",
    )
    parser.add_argument(
        "--detail", action="store_true",
        help="Show full turn-by-turn detail for each session",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of formatted text",
    )

    args = parser.parse_args()

    # Collect session files
    if args.session:
        files = []
        for pattern in args.session:
            files.extend(glob.glob(pattern))
    else:
        files = sorted(glob.glob(str(Path(args.sessions_dir) / "*.jsonl")))

    if not files:
        print(f"No JSONL files found in {args.sessions_dir}/")
        return

    print(f"Found {len(files)} session file(s)")

    all_analyses = []
    for path in sorted(files):
        records = load_session(path)
        if not records:
            continue

        analysis = analyze_session(records)
        all_analyses.append(analysis)

        if args.detail:
            print_session_detail(records, path)

    if args.json:
        print(json.dumps(all_analyses, indent=2))
    else:
        print_aggregate_summary(all_analyses)


if __name__ == "__main__":
    main()
