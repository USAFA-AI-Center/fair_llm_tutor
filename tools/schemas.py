"""Pydantic I/O models for tutor tools.

All tools use str->str (framework constraint) but encode/decode JSON
via these models for structured validation.
"""

from enum import Enum

from pydantic import BaseModel


# --- Shared enums (used by agent prompt, mode detection, etc.) ---

class InteractionMode(str, Enum):
    HINT = "HINT"
    CONCEPT_EXPLANATION = "CONCEPT_EXPLANATION"


class Severity(str, Enum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"


# --- Computational tool I/O ---

class RetrievalInput(BaseModel):
    query: str
    top_k: int = 3


class HistoryCheckInput(BaseModel):
    correct_answer: str
    student_history: list[str] = []


class HintLevelInput(BaseModel):
    severity: str = "Major"
    hint_level_override: int | None = None
    problem_id: str | None = None
    mark_complete: bool | None = None


# --- Conversation state tool I/O ---

class ConversationStateAction(str, Enum):
    GET = "get"
    UPDATE = "update"


class ConversationStateInput(BaseModel):
    action: ConversationStateAction
    set_current_problem: str | None = None
    problem_text: str | None = None
    mark_solved: str | None = None
    increment_correct_turns: bool = False
    reset_correct_turns: bool = False
