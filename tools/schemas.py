"""Pydantic I/O models for tutor tools.

All tools use str->str (framework constraint) but encode/decode JSON
via these models for structured validation.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


# --- Shared enums (used by agent prompt, mode detection, etc.) ---

class InteractionMode(str, Enum):
    HINT = "HINT"
    CONCEPT_EXPLANATION = "CONCEPT_EXPLANATION"


class Severity(str, Enum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"


class SafetyVerdict(str, Enum):
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"


# --- Computational tool I/O ---

class RetrievalInput(BaseModel):
    query: str
    top_k: int = 3


class HistoryCheckInput(BaseModel):
    correct_answer: str
    student_history: List[str] = []


class HintLevelInput(BaseModel):
    severity: str = "Major"
    hint_level_override: Optional[int] = None
