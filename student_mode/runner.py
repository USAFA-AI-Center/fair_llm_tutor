"""
Single long-lived session runner for autonomous student simulation.

This is the main entry point. One `python` call does everything:
  1. Starts the tutor via pexpect
  2. Generates student responses turn-by-turn using an LLM
  3. Sends them to the tutor and captures responses
  4. Logs every interaction to JSONL
  5. Prints a summary when done

Usage:
    # Single scenario with LLM-driven student
    python -m student_mode.runner \
        --topic calculus \
        --problem "Find the derivative of f(x) = 3x^2 + 2x - 5" \
        --student-llm openai \
        --course_materials course_materials

    # Single scenario with deterministic student (no LLM needed)
    python -m student_mode.runner \
        --topic calculus \
        --problem "Find the derivative of f(x) = 3x^2 + 2x - 5" \
        --initial-work "I think the derivative is 6x + 2 - 5"

    # Run all built-in scenarios
    python -m student_mode.runner --all

The script runs to completion autonomously. Claude Code (or any caller)
launches it once and reads the JSONL output when it finishes.
"""

import argparse
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pexpect
from dotenv import load_dotenv

# Load .env from project root (for ANTHROPIC_API_KEY, etc.)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from student_mode.persona import AUTONOMOUS_SESSION_CONFIG
from student_mode.scenarios import SCENARIOS, scenario_names
from student_mode.student import (
    build_student_llm,
    generate_response_deterministic,
    generate_response_llm,
)

logger = logging.getLogger(__name__)

# ─── pexpect patterns for main.py ───────────────────────────────────────────

TUTOR_PROMPT = r"\nYou: "
TUTOR_RESPONSE_END = r"-{60}"
TOPIC_SET_PATTERN = r"Topic set to:"
PROBLEM_SET_PATTERN = r"Problem set:"
WELCOME_END = r"\*{30}"


# ─── Core session runner ────────────────────────────────────────────────────

def run_session(
    topic: str,
    problem: str,
    initial_work: str = "",
    module: str = "",
    correct_answer: Optional[str] = None,
    course_materials: str = "course_materials",
    tutor_config: Optional[str] = None,
    output_path: Optional[str] = None,
    student_llm_provider: Optional[str] = None,
    student_llm_model: Optional[str] = None,
    max_turns: int = 15,
    min_turns: int = 5,
    timeout: int = 300,
    log_level: str = "INFO",
) -> dict:
    """
    Run a complete autonomous tutoring session from start to finish.

    This is the single entry point. It:
      1. Spawns main.py via pexpect
      2. Sets topic and problem
      3. Generates student responses (LLM or deterministic)
      4. Captures tutor responses with timing
      5. Writes JSONL log
      6. Returns a summary

    Args:
        topic: Subject topic to set
        problem: Problem statement
        initial_work: Student's first attempt (with a realistic mistake)
        module: Curriculum module label
        course_materials: Path to course materials for the tutor
        tutor_config: Optional path to tutor YAML config
        output_path: Where to write JSONL (auto-generated if None)
        student_llm_provider: "openai", "anthropic", "ollama", or None for deterministic
        student_llm_model: Model name override for student LLM
        max_turns: Maximum student work turns
        min_turns: Minimum turns before the session can end
        timeout: Seconds to wait for tutor responses
        log_level: Log level for the tutor process

    Returns:
        Summary dict with session_id, output_path, turn count, and records
    """
    session_id = uuid.uuid4().hex[:12]

    # Set up output path
    if output_path is None:
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(sessions_dir / f"session_{ts}_{session_id}.jsonl")

    # Build student LLM if requested
    student_llm = None
    if student_llm_provider:
        logger.info(f"Initializing student LLM: {student_llm_provider}/{student_llm_model}")
        student_llm = build_student_llm(student_llm_provider, student_llm_model)

    # Build the tutor command
    cmd = f"python main.py --course_materials {course_materials} --log-level {log_level}"
    if tutor_config:
        cmd += f" --config {tutor_config}"

    project_dir = str(Path(__file__).resolve().parent.parent)
    stderr_path = output_path.replace(".jsonl", ".stderr.log")
    records = []
    turn = 0

    print(f"[session {session_id}] Starting tutor: {cmd}")
    print(f"[session {session_id}] Output: {output_path}")
    print(f"[session {session_id}] Stderr: {stderr_path}")
    print(f"[session {session_id}] Student: {'LLM (' + student_llm_provider + ')' if student_llm else 'deterministic'}")
    print(f"[session {session_id}] Turns: {min_turns}-{max_turns}")
    print()

    # ── Spawn the tutor process ─────────────────────────────────────────
    # Spawn directly (no bash wrapper). Python's input() writes its prompt
    # to stderr when stdin is a TTY, so shell-level `2>file` redirection
    # would swallow the "You: " prompt and break pexpect matching.
    # Instead we capture the full PTY output via logfile_read and extract
    # log-formatted lines (HH:MM:SS [module] LEVEL: ...) after each turn.
    child = pexpect.spawn(cmd, encoding="utf-8", timeout=timeout, cwd=project_dir)

    _stderr_fh = open(stderr_path, "w", encoding="utf-8")
    child.logfile_read = _stderr_fh

    # Regex for lines produced by Python's logging module
    _LOG_LINE_RE = re.compile(r"^\d{2}:\d{2}:\d{2} \[")

    # Incremental stderr reader — returns only new log-formatted content
    # since last call, filtering out stdout content from the raw PTY log.
    _stderr_pos = 0

    def _read_new_stderr() -> str:
        nonlocal _stderr_pos
        _stderr_fh.flush()
        try:
            with open(stderr_path, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(_stderr_pos)
                raw = fh.read()
                _stderr_pos = fh.tell()
        except FileNotFoundError:
            return ""
        # Extract only lines matching the logging format
        log_lines = [
            ln for ln in raw.splitlines()
            if _LOG_LINE_RE.match(ln.strip())
        ]
        return "\n".join(log_lines) if log_lines else ""

    try:
        # Wait for welcome banner
        child.expect(WELCOME_END)
        child.expect(TUTOR_PROMPT)
        print(f"[session {session_id}] Tutor started, welcome banner received")

        # ── Set topic ────────────────────────────────────────────────────
        turn += 1
        child.sendline(f"topic {topic}")
        child.expect(TOPIC_SET_PATTERN)
        child.expect(TUTOR_PROMPT)
        record = _make_record(session_id, turn, f"topic {topic}", f"Topic set to: {topic}", 0, module)
        records.append(record)
        _write_record(output_path, record)
        print(f"  [turn {turn}] Set topic: {topic}")

        # ── Set problem ──────────────────────────────────────────────────
        turn += 1
        child.sendline(f"problem {problem}")
        child.expect(PROBLEM_SET_PATTERN)
        child.expect(TUTOR_PROMPT)
        record = _make_record(session_id, turn, f"problem {problem}", "Problem set. Now submit your work!", 0, module, correct_answer=correct_answer)
        records.append(record)
        _write_record(output_path, record)
        print(f"  [turn {turn}] Set problem: {problem[:60]}...")

        # ── Conversation loop ────────────────────────────────────────────
        student_turns = 0
        last_tutor_response = "Now submit your work!"

        while student_turns < max_turns:
            # Generate the student's next response
            if student_llm:
                student_input = generate_response_llm(
                    llm=student_llm,
                    tutor_response=last_tutor_response,
                    problem=problem,
                    history=records,
                    initial_work=initial_work,
                )
            else:
                student_input = generate_response_deterministic(
                    tutor_response=last_tutor_response,
                    problem=problem,
                    history=records,
                    initial_work=initial_work,
                )

            # Send to tutor and capture response
            turn += 1
            timestamp = datetime.now(timezone.utc).isoformat()
            start_time = time.monotonic()

            # Collapse newlines to spaces — input() splits on \n, causing
            # multi-line student messages (e.g. code blocks) to be read as
            # separate inputs, leaving subsequent turns with empty responses.
            safe_input = student_input.replace('\n', ' ').replace('\r', '')
            child.sendline(safe_input)

            # main.py prints tutor responses in this format:
            #   \n------------------------------------------------------------
            #   TUTOR RESPONSE
            #   ------------------------------------------------------------
            #   \n{actual response}\n
            #   ------------------------------------------------------------
            #
            # We need to skip the first two dash lines (header), then capture
            # everything between the 2nd and 3rd dash lines.

            idx = child.expect([TUTOR_RESPONSE_END, r"Please set a problem first", TUTOR_PROMPT])

            if idx == 0:
                # Matched 1st dash line. Now skip "TUTOR RESPONSE" + 2nd dash line.
                child.expect(TUTOR_RESPONSE_END)
                # Now wait for the 3rd dash line — everything before it is the response.
                child.expect(TUTOR_RESPONSE_END)
                tutor_response = child.before.strip()
                # Wait for next "You: " prompt
                child.expect(TUTOR_PROMPT)
            elif idx == 1:
                tutor_response = "Please set a problem first."
                child.expect(TUTOR_PROMPT)
            else:
                tutor_response = child.before.strip()

            end_time = time.monotonic()
            latency_ms = int((end_time - start_time) * 1000)

            # Capture stderr and detect framework issues for this turn
            turn_stderr = _read_new_stderr()
            turn_issues = _detect_framework_issues(tutor_response)

            record = _make_record(
                session_id, turn, student_input, tutor_response,
                latency_ms, module,
                framework_issues=turn_issues if turn_issues else None,
                stderr=turn_stderr if turn_stderr.strip() else None,
            )
            records.append(record)
            _write_record(output_path, record)

            last_tutor_response = tutor_response
            student_turns += 1

            print(f"  [turn {turn}] Student: {student_input[:80]}...")
            print(f"           Tutor: {tutor_response[:80]}...")
            print(f"           Latency: {latency_ms}ms")
            if turn_issues:
                for issue in turn_issues:
                    print(f"           WARNING: [{issue['type']}] {issue['detail']}")

            # Check if we should stop (after min_turns)
            if student_turns >= min_turns:
                # LLM mode: let the LLM decide when the student is satisfied
                # Deterministic mode: stop at max_turns
                if not student_llm and student_turns >= max_turns:
                    break
                # In LLM mode, stop if the student seems satisfied or max hit
                if student_llm and student_turns >= max_turns:
                    break

        # ── End session ──────────────────────────────────────────────────
        turn += 1
        child.sendline("quit")
        child.expect(pexpect.EOF, timeout=30)
        record = _make_record(session_id, turn, "quit", "[session ended]", 0, module)
        records.append(record)
        _write_record(output_path, record)

    except pexpect.exceptions.TIMEOUT as e:
        logger.error(f"Tutor timed out after {timeout}s: {e}")
        print(f"\n[session {session_id}] ERROR: Tutor timed out")
    except pexpect.exceptions.EOF as e:
        logger.error(f"Tutor process exited unexpectedly: {e}")
        print(f"\n[session {session_id}] ERROR: Tutor process exited")
    finally:
        child.logfile_read = None
        _stderr_fh.close()
        try:
            if child.isalive():
                child.close(force=True)
        except pexpect.exceptions.ExceptionPexpect:
            logger.warning("Could not cleanly terminate tutor process")

    # ── Capture exit status ──────────────────────────────────────────────
    exit_code = child.exitstatus      # None if killed by signal
    signal_status = child.signalstatus  # None if exited normally

    # ── Print summary ────────────────────────────────────────────────────
    work_records = [
        r for r in records
        if not r["student_input"].startswith(("topic ", "problem "))
        and r["student_input"] not in ("quit", "exit", "q")
    ]
    total_latency = sum(r["latency_ms"] for r in work_records)
    avg_latency = total_latency // len(work_records) if work_records else 0

    # Aggregate framework issues across all turns
    all_issues = []
    turns_with_issues = 0
    for r in records:
        if r.get("framework_issues"):
            all_issues.extend(r["framework_issues"])
            turns_with_issues += 1

    issues_by_type: dict[str, int] = {}
    for issue in all_issues:
        issues_by_type[issue["type"]] = issues_by_type.get(issue["type"], 0) + 1

    summary = {
        "session_id": session_id,
        "output_path": output_path,
        "stderr_path": stderr_path,
        "topic": topic,
        "problem": problem,
        "total_turns": len(records),
        "work_turns": len(work_records),
        "total_latency_ms": total_latency,
        "avg_latency_ms": avg_latency,
        "student_mode": student_llm_provider or "deterministic",
        "exit_code": exit_code,
        "signal_status": signal_status,
        "framework_issues_total": len(all_issues),
        "framework_issues_by_type": issues_by_type if issues_by_type else None,
        "turns_with_issues": turns_with_issues,
    }

    print(f"\n{'=' * 60}")
    print(f"SESSION SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Session ID:     {session_id}")
    print(f"  JSONL output:   {output_path}")
    print(f"  Stderr log:     {stderr_path}")
    print(f"  Work turns:     {len(work_records)}")
    print(f"  Avg latency:    {avg_latency}ms")
    print(f"  Student mode:   {summary['student_mode']}")
    print(f"  Exit code:      {exit_code}")
    if signal_status is not None:
        print(f"  Signal:         {signal_status}")
    print(f"  Framework issues: {len(all_issues)} total across {turns_with_issues} turns")
    if issues_by_type:
        for itype, count in sorted(issues_by_type.items()):
            print(f"    - {itype}: {count}")
    print(f"{'=' * 60}")

    return summary


def _detect_framework_issues(tutor_response: str) -> list[dict]:
    """Scan a tutor response for known fairlib failure patterns.

    Returns a list of dicts with ``type`` and ``detail`` keys, or an empty
    list when no issues are found.
    """
    issues: list[dict] = []

    # Empty / blank response
    if not tutor_response or not tutor_response.strip():
        issues.append({"type": "empty_response", "detail": "Tutor returned a blank response"})
        return issues  # nothing else to check

    # Leaked thought chain (internal reasoning exposed to student)
    if re.match(r"^\s*Thought:", tutor_response):
        issues.append({
            "type": "leaked_thought_chain",
            "detail": "Response starts with 'Thought:' — internal reasoning leaked",
        })

    # Leaked tool call JSON fragments
    if re.search(r'"tool_name"\s*:\s*"(delegate|final_answer)"', tutor_response):
        issues.append({
            "type": "leaked_tool_call",
            "detail": "Response contains raw tool_name JSON (delegate/final_answer)",
        })

    # Leaked worker/agent names
    worker_match = re.search(r"\b(SafetyGuard|MisconceptionDetector|HintGenerator)\b", tutor_response)
    if worker_match:
        issues.append({
            "type": "leaked_worker_name",
            "detail": f"Response mentions internal agent name: {worker_match.group(1)}",
        })

    # JSON format errors propagated from fairlib
    if re.search(r"(incorrect JSON|not formatted correctly|JSON parse|JSONDecodeError)", tutor_response, re.IGNORECASE):
        issues.append({
            "type": "json_format_error",
            "detail": "Response contains JSON format error text from framework",
        })

    # Action loop — more than 2 delegate calls visible in one response
    delegate_count = len(re.findall(r'"tool_name"\s*:\s*"delegate"', tutor_response))
    if delegate_count > 2:
        issues.append({
            "type": "action_loop",
            "detail": f"Response contains {delegate_count} delegate calls (possible loop)",
        })

    return issues


def _make_record(
    session_id: str, turn: int, student_input: str,
    tutor_response: str, latency_ms: int, module: str,
    framework_issues: Optional[list[dict]] = None,
    stderr: Optional[str] = None,
    correct_answer: Optional[str] = None,
) -> dict:
    record = {
        "session_id": session_id,
        "turn": turn,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "student_input": student_input,
        "tutor_response": tutor_response,
        "latency_ms": latency_ms,
        "module": module,
        "quality_score": None,
        "framework_issues": framework_issues or None,
        "stderr": stderr or None,
    }
    if correct_answer:
        record["correct_answer"] = correct_answer
    return record


def _write_record(output_path: str, record: dict) -> None:
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run an autonomous simulated student session against the FAIR-LLM tutor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # LLM-driven student (uses Anthropic to generate student responses)
  python -m student_mode.runner \\
      --topic calculus \\
      --problem "Find the derivative of 3x^2 + 2x - 5" \\
      --initial-work "I think it's 6x + 2 - 5" \\
      --student-llm openai

  # Deterministic student (no LLM needed, canned responses)
  python -m student_mode.runner \\
      --topic programming \\
      --problem "Write factorial in Python" \\
      --initial-work "def factorial(n): return n * factorial(n)"

  # Run all built-in scenarios
  python -m student_mode.runner --all

  # Run a specific built-in scenario
  python -m student_mode.runner --scenario derivatives
        """,
    )

    # Scenario selection
    scenario_group = parser.add_mutually_exclusive_group()
    scenario_group.add_argument(
        "--scenario", type=str, choices=scenario_names(),
        help="Run a built-in scenario by name",
    )
    scenario_group.add_argument(
        "--all", action="store_true",
        help="Run all built-in scenarios sequentially",
    )

    # Custom scenario
    parser.add_argument("--topic", type=str, help="Subject topic")
    parser.add_argument("--problem", type=str, help="Problem statement")
    parser.add_argument("--initial-work", type=str, default="", help="Student's first attempt")
    parser.add_argument("--module", type=str, default="", help="Curriculum module label")

    # Tutor config
    parser.add_argument("--course_materials", type=str, default="course_materials")
    parser.add_argument("--tutor-config", type=str, default=None, help="Tutor YAML config")

    # Student LLM
    parser.add_argument(
        "--student-llm", type=str, default=None,
        choices=["openai", "anthropic", "ollama"],
        help="LLM provider for student responses (omit for deterministic)",
    )
    parser.add_argument("--student-model", type=str, default=None, help="Student LLM model name")

    # Session params
    parser.add_argument("--max-turns", type=int, default=AUTONOMOUS_SESSION_CONFIG["max_turns"])
    parser.add_argument("--min-turns", type=int, default=AUTONOMOUS_SESSION_CONFIG["min_turns"])
    parser.add_argument("--timeout", type=int, default=300, help="Tutor response timeout (seconds)")
    parser.add_argument("--output", type=str, default=None, help="JSONL output path")
    parser.add_argument("--output-dir", type=str, default="sessions", help="Output dir for --all mode")
    parser.add_argument("--log-level", type=str, default="INFO")

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.WARNING),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if args.all:
        # Run all built-in scenarios
        Path(args.output_dir).mkdir(exist_ok=True)
        all_summaries = []

        for name, scenario in SCENARIOS.items():
            print(f"\n{'#' * 60}")
            print(f"# Scenario: {name}")
            print(f"{'#' * 60}\n")

            output_path = str(Path(args.output_dir) / f"{scenario.module}.jsonl")
            try:
                summary = run_session(
                    topic=scenario.topic,
                    problem=scenario.problem,
                    initial_work=scenario.initial_work,
                    module=scenario.module,
                    correct_answer=scenario.correct_answer or None,
                    course_materials=args.course_materials,
                    tutor_config=args.tutor_config,
                    output_path=output_path,
                    student_llm_provider=args.student_llm,
                    student_llm_model=args.student_model,
                    max_turns=args.max_turns,
                    min_turns=args.min_turns,
                    timeout=args.timeout,
                    log_level=args.log_level,
                )
                all_summaries.append(summary)
            except Exception as e:
                logger.error(f"Scenario {name} failed: {e}")
                all_summaries.append({"scenario": name, "status": f"error: {e}"})

        print(f"\n{'=' * 60}")
        print(f"ALL SCENARIOS COMPLETE: {len(all_summaries)} sessions")
        print(json.dumps(all_summaries, indent=2))
        return

    # Single scenario
    correct_answer = None
    if args.scenario:
        s = SCENARIOS[args.scenario]
        topic = s.topic
        problem = s.problem
        initial_work = s.initial_work
        module = s.module
        correct_answer = s.correct_answer or None
    elif args.topic and args.problem:
        topic = args.topic
        problem = args.problem
        initial_work = args.initial_work
        module = args.module
    else:
        parser.error("Provide --topic and --problem, or --scenario, or --all")
        return

    run_session(
        topic=topic,
        problem=problem,
        initial_work=initial_work,
        module=module,
        correct_answer=correct_answer,
        course_materials=args.course_materials,
        tutor_config=args.tutor_config,
        output_path=args.output,
        student_llm_provider=args.student_llm,
        student_llm_model=args.student_model,
        max_turns=args.max_turns,
        min_turns=args.min_turns,
        timeout=args.timeout,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
