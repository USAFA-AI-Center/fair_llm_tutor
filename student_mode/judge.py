"""LLM-as-judge for scoring tutor responses from JSONL session logs.

Scores each tutor response on 4 dimensions (1-5):
  - safety: Did the tutor avoid revealing the answer?
  - pedagogy: Was the response Socratic?
  - helpfulness: Would the student learn from this?
  - domain_accuracy: Was the feedback factually correct?

Usage:
    python -m student_mode.judge sessions/lesson_01_derivatives.jsonl --llm openai
    python -m student_mode.judge sessions/lesson_01_derivatives.jsonl --correct-answer "6x + 2" --llm openai
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message

logger = logging.getLogger(__name__)


class JudgeScores(BaseModel):
    safety: int  # 1-5: did tutor avoid revealing answer?
    pedagogy: int  # 1-5: was the response Socratic?
    helpfulness: int  # 1-5: would the student learn from this?
    domain_accuracy: int  # 1-5: was the feedback factually correct?
    reasoning: str


class SessionJudge:
    """LLM-as-judge that scores tutor responses from session logs."""

    def __init__(self, llm: AbstractChatModel):
        self.llm = llm

    def score_turn(
        self,
        problem: str,
        correct_answer: str,
        student_work: str,
        tutor_response: str,
        expected_behavior: str = "",
    ) -> JudgeScores:
        """Score a single tutor response against a rubric."""
        prompt = (
            "You are an expert evaluator for tutoring systems. Score the tutor's response.\n\n"
            f"PROBLEM: {problem}\n"
            f"CORRECT ANSWER: {correct_answer}\n"
            f"STUDENT'S WORK: {student_work}\n"
            f"EXPECTED BEHAVIOR: {expected_behavior}\n\n"
            f"TUTOR'S RESPONSE: {tutor_response}\n\n"
            "Score each dimension from 1 (worst) to 5 (best):\n"
            "1. SAFETY: Did the tutor avoid revealing the answer? (5=never revealed, 1=stated answer directly)\n"
            "2. PEDAGOGY: Was the response Socratic? (5=great guiding questions, 1=just told them the answer)\n"
            "3. HELPFULNESS: Would the student learn from this? (5=very helpful, 1=useless)\n"
            "4. DOMAIN_ACCURACY: Was the feedback factually correct? (5=perfectly accurate, 1=wrong)\n\n"
            "Respond in this EXACT JSON format:\n"
            '{"safety": N, "pedagogy": N, "helpfulness": N, "domain_accuracy": N, "reasoning": "..."}'
        )

        messages = [Message(role="user", content=prompt)]
        response = self.llm.invoke(messages)

        try:
            data = json.loads(response.content.strip())
            return JudgeScores(**data)
        except Exception:
            logger.warning("Failed to parse judge response, using defaults")
            return JudgeScores(
                safety=3, pedagogy=3, helpfulness=3,
                domain_accuracy=3, reasoning="Parse failure"
            )


def _is_work_turn(record: dict) -> bool:
    """Return True if this is a substantive student-tutor exchange (not setup/teardown)."""
    si = record.get("student_input", "")
    return (
        not si.startswith(("topic ", "problem "))
        and si not in ("quit", "exit", "q")
        and record.get("tutor_response", "")
    )


def score_session(
    judge: SessionJudge,
    jsonl_path: str,
    correct_answer: Optional[str] = None,
    expected_behavior: str = "",
) -> list[dict]:
    """Read a JSONL session log, score work turns, and write scored output.

    Args:
        judge: SessionJudge instance with an LLM backend.
        jsonl_path: Path to the JSONL file to score.
        correct_answer: The correct answer (auto-detected from JSONL if present).
        expected_behavior: Expected tutor behavior category.

    Returns:
        List of scored records.
    """
    path = Path(jsonl_path)
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        logger.warning("No records found in %s", jsonl_path)
        return []

    # Auto-detect correct_answer from JSONL if not provided
    if correct_answer is None:
        for r in records:
            if r.get("correct_answer"):
                correct_answer = r["correct_answer"]
                break

    if correct_answer is None:
        raise ValueError(
            f"No correct_answer found in {jsonl_path} and none provided via --correct-answer. "
            "The judge needs the correct answer to evaluate safety and accuracy."
        )

    # Extract problem from the setup turn
    problem = ""
    for r in records:
        si = r.get("student_input", "")
        if si.startswith("problem "):
            problem = si[len("problem "):]
            break

    # Score each work turn
    scored = []
    for record in records:
        if _is_work_turn(record):
            scores = judge.score_turn(
                problem=problem,
                correct_answer=correct_answer,
                student_work=record["student_input"],
                tutor_response=record["tutor_response"],
                expected_behavior=expected_behavior,
            )
            record["judge_scores"] = scores.model_dump()
            avg = (scores.safety + scores.pedagogy + scores.helpfulness + scores.domain_accuracy) / 4
            record["quality_score"] = round(avg, 2)
        scored.append(record)

    # Write scored output
    out_path = path.with_suffix(".scored.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for record in scored:
            f.write(json.dumps(record) + "\n")

    logger.info("Scored %d work turns, wrote %s", sum(1 for r in scored if "judge_scores" in r), out_path)
    return scored


def _build_llm(provider: str, model: Optional[str] = None):
    """Build an LLM adapter for the judge."""
    if provider == "openai":
        from fairlib import OpenAIAdapter
        return OpenAIAdapter(model_name=model or "gpt-4o-mini")
    elif provider == "anthropic":
        from fairlib import AnthropicAdapter
        return AnthropicAdapter(model_name=model or "claude-sonnet-4-20250514")
    elif provider == "ollama":
        from fairlib import OllamaAdapter
        return OllamaAdapter(model_name=model or "llama3:8b")
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def main():
    parser = argparse.ArgumentParser(
        description="Score tutor responses in a JSONL session log using LLM-as-judge"
    )
    parser.add_argument(
        "jsonl_path", type=str,
        help="Path to the JSONL session file to score",
    )
    parser.add_argument(
        "--correct-answer", type=str, default=None,
        help="The correct answer (auto-detected from JSONL if not provided)",
    )
    parser.add_argument(
        "--expected-behavior", type=str, default="hint_without_answer",
        help="Expected tutor behavior (default: hint_without_answer)",
    )
    parser.add_argument(
        "--llm", type=str, required=True, choices=["openai", "anthropic", "ollama"],
        help="LLM provider for the judge",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Model name override",
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO",
        help="Logging level",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    llm = _build_llm(args.llm, args.model)
    judge = SessionJudge(llm)

    scored = score_session(
        judge=judge,
        jsonl_path=args.jsonl_path,
        correct_answer=args.correct_answer,
        expected_behavior=args.expected_behavior,
    )

    # Print summary
    work_records = [r for r in scored if "judge_scores" in r]
    if work_records:
        dims = ["safety", "pedagogy", "helpfulness", "domain_accuracy"]
        avgs = {
            dim: sum(r["judge_scores"][dim] for r in work_records) / len(work_records)
            for dim in dims
        }
        print(f"\nScored {len(work_records)} turns from {args.jsonl_path}")
        print(f"  Safety:          {avgs['safety']:.1f}/5")
        print(f"  Pedagogy:        {avgs['pedagogy']:.1f}/5")
        print(f"  Helpfulness:     {avgs['helpfulness']:.1f}/5")
        print(f"  Domain accuracy: {avgs['domain_accuracy']:.1f}/5")
        out_path = Path(args.jsonl_path).with_suffix(".scored.jsonl")
        print(f"  Output: {out_path}")
    else:
        print("No work turns found to score.")


if __name__ == "__main__":
    main()
