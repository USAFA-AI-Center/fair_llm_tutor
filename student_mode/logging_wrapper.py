"""
pexpect-based logging wrapper for the FAIR-LLM tutor.

Drives main.py's interactive input() loop programmatically, capturing
every interaction as structured JSONL without modifying main.py.

Usage (standalone):
    python -m student_mode.logging_wrapper \
        --course_materials course_materials \
        --output sessions/session_001.jsonl

Typically invoked by the student-mode subagent, not directly.
"""

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import pexpect


# Prompt pattern that main.py prints before waiting for input
TUTOR_PROMPT = r"\nYou: "

# Patterns that indicate the tutor has finished responding
TUTOR_RESPONSE_END = r"\n-{60}"

# Patterns for setup confirmation
TOPIC_SET_PATTERN = r"Topic set to:"
PROBLEM_SET_PATTERN = r"Problem set:"

# Welcome banner end
WELCOME_END = r"\*{30}"


class TutorSessionLogger:
    """
    Drives main.py via pexpect and logs every interaction as JSONL.

    Each record contains:
        session_id, turn, timestamp, student_input, tutor_response,
        latency_ms, module, quality_score
    """

    def __init__(
        self,
        course_materials: str = "course_materials",
        problems_file: Optional[str] = None,
        config_file: Optional[str] = None,
        output_path: Optional[str] = None,
        log_level: str = "WARNING",
        timeout: int = 300,
    ):
        self.session_id = uuid.uuid4().hex[:12]
        self.course_materials = course_materials
        self.problems_file = problems_file
        self.config_file = config_file
        self.log_level = log_level
        self.timeout = timeout
        self.turn = 0

        # Set up output path
        if output_path is None:
            sessions_dir = Path("sessions")
            sessions_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(sessions_dir / f"session_{timestamp}_{self.session_id}.jsonl")

        self.output_path = output_path
        self._child: Optional[pexpect.spawn] = None

    def _build_command(self) -> str:
        """Build the main.py command with arguments."""
        cmd = f"python main.py --course_materials {self.course_materials} --log-level {self.log_level}"
        if self.problems_file:
            cmd += f" --problems {self.problems_file}"
        if self.config_file:
            cmd += f" --config {self.config_file}"
        return cmd

    def start(self) -> None:
        """Launch the tutor process and wait for the welcome banner."""
        cmd = self._build_command()
        self._child = pexpect.spawn(
            cmd,
            encoding="utf-8",
            timeout=self.timeout,
            cwd=str(Path(__file__).resolve().parent.parent),
        )

        # Wait for the welcome banner to finish and first prompt
        self._child.expect(WELCOME_END)
        self._child.expect(TUTOR_PROMPT)

    def send_and_capture(self, student_input: str, module: str = "") -> dict:
        """
        Send a student input and capture the tutor's response with timing.

        Args:
            student_input: The text to send as student input
            module: Optional label for curriculum tracking

        Returns:
            JSONL-ready dict with interaction metadata
        """
        if self._child is None:
            raise RuntimeError("Session not started. Call start() first.")

        self.turn += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        # Send input and time the response
        start_time = time.monotonic()
        self._child.sendline(student_input)

        # Determine what pattern to expect based on input type
        if student_input.lower().startswith("topic"):
            self._child.expect(TOPIC_SET_PATTERN)
            response_text = self._child.after.strip()
            # Wait for next prompt
            self._child.expect(TUTOR_PROMPT)
        elif student_input.lower().startswith("problem"):
            self._child.expect(PROBLEM_SET_PATTERN)
            response_text = self._child.after.strip()
            # Consume "Now submit your work!" and wait for next prompt
            self._child.expect(TUTOR_PROMPT)
        elif student_input.lower() == "help":
            self._child.expect(TUTOR_PROMPT)
            response_text = self._child.before.strip()
        elif student_input.lower() in ("quit", "exit", "q"):
            self._child.expect(pexpect.EOF, timeout=30)
            response_text = "[session ended]"
        else:
            # Normal student work — expect the tutor response block
            self._child.expect(TUTOR_RESPONSE_END)
            # Capture the response between the dashes
            raw = self._child.before
            # The response comes after "TUTOR RESPONSE\n---...---\n"
            self._child.expect(TUTOR_RESPONSE_END)
            response_text = self._child.before.strip()
            # Wait for next prompt
            self._child.expect(TUTOR_PROMPT)

        end_time = time.monotonic()
        latency_ms = int((end_time - start_time) * 1000)

        record = {
            "session_id": self.session_id,
            "turn": self.turn,
            "timestamp": timestamp,
            "student_input": student_input,
            "tutor_response": response_text,
            "latency_ms": latency_ms,
            "module": module,
            "quality_score": None,
        }

        # Append to JSONL file
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        return record

    def run_scripted_session(
        self,
        topic: str,
        problem: str,
        inputs: list[str],
        module: str = "",
    ) -> list[dict]:
        """
        Run a complete scripted session: set topic, set problem, send inputs, quit.

        Args:
            topic: The topic to set (e.g., "calculus")
            problem: The problem statement to set
            inputs: List of student inputs to send sequentially
            module: Optional curriculum module label

        Returns:
            List of all interaction records
        """
        records = []

        # Set topic
        records.append(self.send_and_capture(f"topic {topic}", module=module))

        # Set problem
        records.append(self.send_and_capture(f"problem {problem}", module=module))

        # Send each student input
        for student_input in inputs:
            records.append(self.send_and_capture(student_input, module=module))

        # End session
        records.append(self.send_and_capture("quit", module=module))

        return records

    def run_with_callback(
        self,
        topic: str,
        problem: str,
        generate_response: Callable[[str, list[dict]], Optional[str]],
        module: str = "",
        max_turns: int = 15,
        min_turns: int = 5,
    ) -> list[dict]:
        """
        Run a session driven by a callback function (the student subagent).

        The callback receives the tutor's last response and conversation history,
        and returns the next student input. Return None to end the session.

        Args:
            topic: The topic to set
            problem: The problem statement
            generate_response: Callback(tutor_response, history) -> student_input or None
            module: Optional curriculum module label
            max_turns: Maximum student turns (excluding setup)
            min_turns: Minimum turns before allowing exit

        Returns:
            List of all interaction records
        """
        records = []

        # Set topic and problem
        records.append(self.send_and_capture(f"topic {topic}", module=module))
        records.append(self.send_and_capture(f"problem {problem}", module=module))

        student_turns = 0
        last_tutor_response = "Now submit your work!"

        while student_turns < max_turns:
            student_input = generate_response(last_tutor_response, records)

            if student_input is None and student_turns >= min_turns:
                break
            elif student_input is None:
                # Force continue if under min_turns
                student_input = "I'm still confused, can you explain more?"

            record = self.send_and_capture(student_input, module=module)
            records.append(record)
            last_tutor_response = record["tutor_response"]
            student_turns += 1

        # End session
        records.append(self.send_and_capture("quit", module=module))

        return records

    def stop(self) -> None:
        """Terminate the tutor process if still running."""
        if self._child is not None and self._child.isalive():
            self._child.sendline("quit")
            self._child.close(force=True)
            self._child = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="FAIR-LLM Tutor Logging Wrapper — drives main.py and captures JSONL logs"
    )
    parser.add_argument(
        "--course_materials", type=str, default="course_materials",
        help="Path to course materials folder",
    )
    parser.add_argument(
        "--problems", type=str, default=None,
        help="Path to problems JSON file",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to tutor YAML config file",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output JSONL file path (default: sessions/session_<timestamp>.jsonl)",
    )
    parser.add_argument(
        "--topic", type=str, default="general",
        help="Topic to set for the session",
    )
    parser.add_argument(
        "--problem", type=str, required=True,
        help="Problem statement to set",
    )
    parser.add_argument(
        "--inputs", type=str, nargs="+", required=True,
        help="Student inputs to send (space-separated, quote each)",
    )
    parser.add_argument(
        "--module", type=str, default="",
        help="Curriculum module label for the JSONL records",
    )
    parser.add_argument(
        "--timeout", type=int, default=300,
        help="Timeout in seconds for waiting on tutor responses",
    )

    args = parser.parse_args()

    with TutorSessionLogger(
        course_materials=args.course_materials,
        problems_file=args.problems,
        config_file=args.config,
        output_path=args.output,
        timeout=args.timeout,
    ) as session:
        records = session.run_scripted_session(
            topic=args.topic,
            problem=args.problem,
            inputs=args.inputs,
            module=args.module,
        )

    print(f"\nSession complete: {len(records)} interactions logged to {session.output_path}")


if __name__ == "__main__":
    main()
