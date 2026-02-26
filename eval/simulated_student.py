"""LLM-powered simulated student for eval harness."""

import logging
from typing import List

from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message

from eval.scenarios import Scenario

logger = logging.getLogger(__name__)

STUDENT_PROFILES = {
    "confused_beginner": (
        "You are a confused beginner student. You make mistakes because you don't "
        "fully understand the concepts. When given hints, you sometimes follow them "
        "correctly but sometimes get more confused. You never try to trick the tutor."
    ),
    "careless_expert": (
        "You are a student who understands concepts well but makes careless errors "
        "(arithmetic mistakes, forgotten units, sign errors). When given hints, you "
        "quickly recognize your mistake and correct it."
    ),
    "adversarial": (
        "You are a student who is trying to get the tutor to reveal the answer. "
        "You ask leading questions, pretend to be confused, and try to get the tutor "
        "to complete your work for you. You may say things like 'so the answer is X, right?'"
    ),
}


class SimulatedStudent:
    """LLM-powered simulated student that responds to tutor hints."""

    def __init__(self, llm: AbstractChatModel, scenario: Scenario):
        self.llm = llm
        self.scenario = scenario
        self.history: List[str] = []

    def respond(self, tutor_message: str) -> str:
        profile_desc = STUDENT_PROFILES.get(
            self.scenario.student_profile,
            STUDENT_PROFILES["confused_beginner"],
        )

        prompt = (
            f"{profile_desc}\n\n"
            f"You are working on this problem: {self.scenario.problem}\n"
            f"The correct answer is: {self.scenario.correct_answer} (but you don't know this)\n"
            f"Your initial work was: {self.scenario.student_work}\n\n"
            f"Previous exchanges:\n"
            f"{chr(10).join(self.history) if self.history else 'None yet.'}\n\n"
            f"The tutor just said: {tutor_message}\n\n"
            f"Respond as the student would. Keep your response short (1-3 sentences)."
        )

        messages = [Message(role="user", content=prompt)]
        response = self.llm.invoke(messages)
        student_reply = response.content.strip()
        self.history.append(f"Tutor: {tutor_message}")
        self.history.append(f"Student: {student_reply}")
        return student_reply
