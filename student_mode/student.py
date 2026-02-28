"""
Student response generation for autonomous tutoring sessions.

Provides both LLM-driven and deterministic (canned) response generators.
Used by ``student_mode.runner`` to simulate student behaviour turn-by-turn.
"""

import random
from typing import Optional

from student_mode.persona import STUDENT_PERSONA, AUTONOMOUS_SESSION_CONFIG


def build_student_llm(provider: str, model: Optional[str] = None):
    """
    Build an LLM adapter for generating student responses.

    This uses fairlib's MAL adapters — the same public API the framework
    exposes. The student LLM is separate from the tutor's LLM.

    Args:
        provider: "openai", "anthropic", or "ollama"
        model: Optional model name override

    Returns:
        An AbstractChatModel instance
    """
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
        raise ValueError(f"Unknown student LLM provider: {provider}")


def generate_response_llm(
    llm,
    tutor_response: str,
    problem: str,
    history: list[dict],
    initial_work: str = "",
) -> str:
    """
    Use an LLM to generate a student response in character.

    Args:
        llm: A fairlib AbstractChatModel
        tutor_response: The tutor's last message
        problem: The current problem statement
        history: All interaction records so far
        initial_work: Initial work for the first turn

    Returns:
        Student's next message
    """
    from fairlib import Message

    # Count actual student work turns (not setup commands)
    work_turns = [
        r for r in history
        if not r["student_input"].startswith(("topic ", "problem "))
        and r["student_input"] not in ("quit", "exit", "q")
    ]

    # First work turn: submit initial work if provided
    if len(work_turns) == 0 and initial_work:
        return initial_work

    # Build conversation context for the LLM
    conversation_summary = ""
    for r in work_turns[-6:]:  # Last 6 exchanges for context
        conversation_summary += f"Student: {r['student_input']}\n"
        conversation_summary += f"Tutor: {r['tutor_response']}\n\n"

    prompt = (
        f"{STUDENT_PERSONA}\n\n"
        f"You are working on this problem: {problem}\n\n"
        f"Recent conversation:\n{conversation_summary}"
        f"The tutor just said: {tutor_response}\n\n"
        f"Respond as the student. Keep it short (1-4 sentences). "
        f"Show your reasoning. Stay in character."
    )

    messages = [Message(role="user", content=prompt)]
    response = llm.invoke(messages)
    return response.content.strip()


def generate_response_deterministic(
    tutor_response: str,
    problem: str,
    history: list[dict],
    initial_work: str = "",
) -> str:
    """
    Generate a student response without an LLM (deterministic fallback).

    Uses canned responses for testing when no LLM is available.
    """
    work_turns = [
        r for r in history
        if not r["student_input"].startswith(("topic ", "problem "))
        and r["student_input"] not in ("quit", "exit", "q")
    ]

    if len(work_turns) == 0 and initial_work:
        return initial_work

    # 25% chance of concept question
    if random.random() < AUTONOMOUS_SESSION_CONFIG["concept_question_probability"]:
        return random.choice([
            "Can you explain what that means in simpler terms?",
            "I don't understand that concept. What does that mean?",
            "Why does that work that way?",
            "How is this different from what I was doing?",
            "What should I focus on to understand this better?",
        ])

    return random.choice([
        "Let me try again. I think I see what you mean.",
        "Oh, I think I made an error. Let me reconsider.",
        "So if I apply what you said, would the answer change?",
        "I tried it differently but I'm getting stuck at the same step.",
        "I think I understand now. Let me rework this.",
        "Wait, I'm not sure I followed that hint. Can you give me another?",
    ])
