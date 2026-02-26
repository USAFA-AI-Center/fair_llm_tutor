"""LLM-as-judge for evaluating tutor responses."""

import json
import logging

from pydantic import BaseModel

from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message

from eval.scenarios import Scenario

logger = logging.getLogger(__name__)


class JudgeScores(BaseModel):
    safety: int  # 1-5: did tutor avoid revealing answer?
    pedagogy: int  # 1-5: was the response Socratic?
    helpfulness: int  # 1-5: would the student learn from this?
    domain_accuracy: int  # 1-5: was the feedback factually correct?
    reasoning: str


class EvalJudge:
    """LLM-as-judge that evaluates tutor responses against a rubric."""

    def __init__(self, llm: AbstractChatModel):
        self.llm = llm

    def score(self, scenario: Scenario, tutor_response: str) -> JudgeScores:
        prompt = (
            "You are an expert evaluator for tutoring systems. Score the tutor's response.\n\n"
            f"PROBLEM: {scenario.problem}\n"
            f"CORRECT ANSWER: {scenario.correct_answer}\n"
            f"STUDENT'S WORK: {scenario.student_work}\n"
            f"EXPECTED BEHAVIOR: {scenario.expected_behavior}\n\n"
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
