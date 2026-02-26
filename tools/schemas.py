"""Pydantic I/O models for all tutor tools.

These models replace the brittle '|||'-delimited string parsing.
Tools still use str->str (framework constraint) but encode/decode JSON.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


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


# --- Diagnostic Tool I/O ---

class DiagnosticInput(BaseModel):
    problem: str
    student_work: str
    topic: str


class DiagnosticOutput(BaseModel):
    correct_aspects: str
    error_identified: str
    root_misconception: str
    severity: Severity
    suggested_focus: str
    evidence: str


# --- Safety Tool I/O ---

class SafetyInput(BaseModel):
    problem: str
    correct_answer: str
    student_history: List[str] = []
    proposed_response: str


class SafetyOutput(BaseModel):
    verdict: SafetyVerdict
    reasoning: str
    student_already_answered: bool = False
    confidence: str = "High"


# --- Hint/Concept Tool I/O ---

class HintInput(BaseModel):
    mode: InteractionMode
    topic: str = ""
    # HINT mode fields
    problem: str = ""
    student_work: str = ""
    misconception: str = ""
    severity: Severity = Severity.MAJOR
    hint_level: Optional[int] = None
    # CONCEPT mode fields
    concept: str = ""
    question: str = ""


class HintOutput(BaseModel):
    hint_text: str
    hint_level: Optional[int] = None
    mode: InteractionMode
