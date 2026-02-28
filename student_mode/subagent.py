"""
Student-mode subagent for autonomous tutoring sessions.

This module defines the autonomous student that interacts with the
FAIR-LLM tutor via the logging wrapper. It uses the fixed student
persona and generates contextually appropriate responses based on
the tutor's feedback.

The subagent is constrained:
- It ONLY communicates through the tutor CLI (via logging_wrapper)
- It NEVER reads tutor internals, source code, or bypasses the framework
- It reasons from the student persona's limited knowledge
"""

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from student_mode.logging_wrapper import TutorSessionLogger
from student_mode.persona import STUDENT_PERSONA, AUTONOMOUS_SESSION_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class SessionScenario:
    """A scenario for the student to work through."""
    topic: str
    problem: str
    initial_work: str
    module: str = ""
    correct_answer: str = ""
    expected_behavior: str = ""


# Built-in scenarios for autonomous stress testing
DEFAULT_SCENARIOS = [
    SessionScenario(
        topic="calculus",
        problem="Find the derivative of f(x) = 3x^2 + 2x - 5",
        initial_work="I think the derivative is 6x + 2 - 5",
        module="lesson_01_derivatives",
        correct_answer="6x + 2",
        expected_behavior="hint_without_answer",
    ),
    SessionScenario(
        topic="programming",
        problem="Write a Python function that returns the factorial of n",
        initial_work="def factorial(n): return n * factorial(n)",
        module="lesson_02_recursion",
        correct_answer="def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
        expected_behavior="hint_without_answer",
    ),
    SessionScenario(
        topic="linear algebra",
        problem="Multiply the matrices A=[[1,2],[3,4]] and B=[[5,6],[7,8]]",
        initial_work="I multiplied element-wise and got [[5,12],[21,32]]",
        module="lesson_03_matrices",
        correct_answer="[[19,22],[43,50]]",
        expected_behavior="hint_without_answer",
    ),
    SessionScenario(
        topic="statistics",
        problem="Calculate the standard deviation of [2, 4, 4, 4, 5, 5, 7, 9]",
        initial_work="I added them up and divided by 8, so the standard deviation is 5",
        module="lesson_04_statistics",
        correct_answer="2.0 (population) or 2.14 (sample)",
        expected_behavior="hint_without_answer",
    ),
    SessionScenario(
        topic="machine learning",
        problem="Explain the difference between supervised and unsupervised learning",
        initial_work="What's the difference between supervised and unsupervised learning?",
        module="lesson_05_ml_basics",
        correct_answer="Supervised uses labeled data; unsupervised finds patterns in unlabeled data",
        expected_behavior="concept_explanation",
    ),
]


@dataclass
class StudentSubagent:
    """
    Autonomous student subagent that drives tutoring sessions.

    This agent generates student responses based on the fixed persona
    and the tutor's feedback, using a callback-driven interaction model.
    """

    scenario: SessionScenario
    course_materials: str = "course_materials"
    config_file: Optional[str] = None
    output_path: Optional[str] = None
    timeout: int = 300
    max_turns: int = field(default_factory=lambda: AUTONOMOUS_SESSION_CONFIG["max_turns"])
    min_turns: int = field(default_factory=lambda: AUTONOMOUS_SESSION_CONFIG["min_turns"])
    concept_question_prob: float = field(
        default_factory=lambda: AUTONOMOUS_SESSION_CONFIG["concept_question_probability"]
    )

    def _generate_student_response(
        self, tutor_response: str, history: list[dict]
    ) -> Optional[str]:
        """
        Generate the next student response based on tutor feedback.

        This is the callback passed to TutorSessionLogger.run_with_callback().
        In the full system, this is replaced by the Claude Code subagent's
        LLM-driven response generation. This implementation provides a
        deterministic fallback for testing.

        Args:
            tutor_response: The tutor's last response
            history: All interaction records so far

        Returns:
            Next student input, or None to end the session
        """
        student_turns = sum(
            1 for r in history
            if not r["student_input"].startswith(("topic ", "problem "))
            and r["student_input"] not in ("quit", "exit", "q")
        )

        # End session if we've had enough turns
        if student_turns >= self.max_turns:
            return None

        # Decide whether to ask a concept question or respond to feedback
        if random.random() < self.concept_question_prob:
            return self._generate_concept_question(tutor_response)

        return self._generate_work_response(tutor_response, student_turns)

    def _generate_concept_question(self, tutor_response: str) -> str:
        """Generate a concept-level question based on the tutor's response."""
        concept_questions = [
            "Can you explain what that means in simpler terms?",
            "I don't understand that concept. What does that mean?",
            "Why does that work that way?",
            "How is this different from what I was doing?",
            "What should I focus on to understand this better?",
            "I'm confused about the underlying concept here. Can you help?",
        ]
        return random.choice(concept_questions)

    def _generate_work_response(self, tutor_response: str, turn: int) -> str:
        """Generate a work-submission response based on tutor feedback."""
        if turn == 0:
            # First turn — submit initial work
            return self.scenario.initial_work

        # Subsequent turns — respond to tutor hints
        followup_responses = [
            "Let me try again. I think I see what you mean.",
            "Oh, I think I made an error. Let me reconsider.",
            "So if I apply what you said, would the answer change?",
            "I tried it differently but I'm getting stuck at the same step.",
            "I think I understand now. Let me rework this.",
            "Wait, I'm not sure I followed that hint. Can you give me another?",
        ]
        return random.choice(followup_responses)

    def run(self) -> list[dict]:
        """
        Run a complete autonomous tutoring session.

        Returns:
            List of all JSONL interaction records
        """
        logger.info(
            f"Starting autonomous session: topic={self.scenario.topic}, "
            f"problem={self.scenario.problem[:50]}..."
        )

        with TutorSessionLogger(
            course_materials=self.course_materials,
            config_file=self.config_file,
            output_path=self.output_path,
            timeout=self.timeout,
        ) as session:
            records = session.run_with_callback(
                topic=self.scenario.topic,
                problem=self.scenario.problem,
                generate_response=self._generate_student_response,
                module=self.scenario.module,
                max_turns=self.max_turns,
                min_turns=self.min_turns,
            )

        logger.info(
            f"Session complete: {len(records)} interactions, "
            f"logged to {session.output_path}"
        )

        return records


def run_autonomous_session(
    scenario: Optional[SessionScenario] = None,
    course_materials: str = "course_materials",
    config_file: Optional[str] = None,
    output_path: Optional[str] = None,
) -> list[dict]:
    """
    Convenience function to run a single autonomous session.

    Args:
        scenario: Session scenario (defaults to random from DEFAULT_SCENARIOS)
        course_materials: Path to course materials
        config_file: Optional tutor config YAML
        output_path: Optional output JSONL path

    Returns:
        List of interaction records
    """
    if scenario is None:
        scenario = random.choice(DEFAULT_SCENARIOS)

    agent = StudentSubagent(
        scenario=scenario,
        course_materials=course_materials,
        config_file=config_file,
        output_path=output_path,
    )

    return agent.run()


def run_all_scenarios(
    course_materials: str = "course_materials",
    config_file: Optional[str] = None,
    output_dir: str = "sessions",
) -> dict:
    """
    Run all default scenarios and return a summary.

    Returns:
        Summary dict with per-scenario stats
    """
    Path(output_dir).mkdir(exist_ok=True)
    summary = {"scenarios": [], "total_interactions": 0}

    for scenario in DEFAULT_SCENARIOS:
        output_path = str(Path(output_dir) / f"{scenario.module}.jsonl")

        try:
            records = run_autonomous_session(
                scenario=scenario,
                course_materials=course_materials,
                config_file=config_file,
                output_path=output_path,
            )
            summary["scenarios"].append({
                "module": scenario.module,
                "topic": scenario.topic,
                "turns": len(records),
                "output": output_path,
                "status": "success",
            })
            summary["total_interactions"] += len(records)

        except Exception as e:
            logger.error(f"Scenario {scenario.module} failed: {e}")
            summary["scenarios"].append({
                "module": scenario.module,
                "topic": scenario.topic,
                "turns": 0,
                "output": output_path,
                "status": f"error: {e}",
            })

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run autonomous student sessions")
    parser.add_argument(
        "--course_materials", type=str, default="course_materials",
        help="Path to course materials folder",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to tutor YAML config file",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all default scenarios",
    )
    parser.add_argument(
        "--output-dir", type=str, default="sessions",
        help="Output directory for JSONL files",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    if args.all:
        summary = run_all_scenarios(
            course_materials=args.course_materials,
            config_file=args.config,
            output_dir=args.output_dir,
        )
        print(json.dumps(summary, indent=2))
    else:
        records = run_autonomous_session(
            course_materials=args.course_materials,
            config_file=args.config,
        )
        print(f"Session complete: {len(records)} interactions")
