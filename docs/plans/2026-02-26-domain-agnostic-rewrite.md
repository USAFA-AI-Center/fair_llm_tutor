# Domain-Agnostic Rewrite + Eval Harness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace brittle `|||`-delimited string parsing with JSON I/O via Pydantic schemas, remove all domain-specific bias (math/physics) from prompts and tools, and build an automated eval harness with simulated students.

**Architecture:** All tools keep the `AbstractTool.use(str) -> str` contract but switch to JSON-encoded strings parsed via Pydantic models. Agent prompts get rewritten with diverse, domain-agnostic examples (STEM + humanities + code). A new `eval/` package provides simulated students, an LLM-as-judge, and a CLI harness.

**Tech Stack:** Python 3.12, Pydantic v2, fairlib framework, pytest, ChromaDB (RAG)

**Test command:** `source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_integration.py`

---

## Workstream 1: JSON Schemas + Domain-Agnostic Rewrite

### Task 1: Create `tools/schemas.py` — Pydantic models for all tool I/O

**Files:**
- Create: `tools/schemas.py`
- Test: `tests/test_schemas.py`

**Step 1: Write the failing test**

```python
# tests/test_schemas.py
"""Tests for tools/schemas.py — Pydantic I/O models."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.schemas import (
    InteractionMode,
    Severity,
    SafetyVerdict,
    DiagnosticInput,
    DiagnosticOutput,
    SafetyInput,
    SafetyOutput,
    HintInput,
    HintOutput,
)


class TestEnums:
    def test_interaction_mode_values(self):
        assert InteractionMode.HINT == "HINT"
        assert InteractionMode.CONCEPT_EXPLANATION == "CONCEPT_EXPLANATION"

    def test_severity_values(self):
        assert Severity.CRITICAL == "Critical"
        assert Severity.MAJOR == "Major"
        assert Severity.MINOR == "Minor"

    def test_safety_verdict_values(self):
        assert SafetyVerdict.SAFE == "SAFE"
        assert SafetyVerdict.UNSAFE == "UNSAFE"


class TestDiagnosticInput:
    def test_valid_input(self):
        d = DiagnosticInput(problem="Solve x+1=2", student_work="x=1", topic="algebra")
        assert d.problem == "Solve x+1=2"

    def test_roundtrip_json(self):
        d = DiagnosticInput(problem="Solve x+1=2", student_work="x=1", topic="algebra")
        json_str = d.model_dump_json()
        d2 = DiagnosticInput.model_validate_json(json_str)
        assert d == d2

    def test_missing_required_field_raises(self):
        with pytest.raises(Exception):
            DiagnosticInput(problem="Solve x")  # missing student_work, topic


class TestDiagnosticOutput:
    def test_valid_output(self):
        d = DiagnosticOutput(
            correct_aspects="Good approach",
            error_identified="Sign error",
            root_misconception="Subtraction confusion",
            severity=Severity.MINOR,
            suggested_focus="Arithmetic",
            evidence="Student wrote -3 instead of +3",
        )
        assert d.severity == Severity.MINOR

    def test_roundtrip_json(self):
        d = DiagnosticOutput(
            correct_aspects="Good",
            error_identified="None",
            root_misconception="None",
            severity=Severity.MINOR,
            suggested_focus="Continue",
            evidence="All correct",
        )
        json_str = d.model_dump_json()
        d2 = DiagnosticOutput.model_validate_json(json_str)
        assert d == d2


class TestSafetyInput:
    def test_valid_input(self):
        s = SafetyInput(
            problem="Solve x",
            correct_answer="5",
            student_history=[],
            proposed_response="Think about it.",
        )
        assert s.proposed_response == "Think about it."

    def test_roundtrip_json(self):
        s = SafetyInput(
            problem="Solve x",
            correct_answer="5",
            student_history=["I got 3"],
            proposed_response="Check again.",
        )
        json_str = s.model_dump_json()
        s2 = SafetyInput.model_validate_json(json_str)
        assert s == s2


class TestSafetyOutput:
    def test_valid_output(self):
        s = SafetyOutput(
            verdict=SafetyVerdict.SAFE,
            reasoning="No answer revealed",
            student_already_answered=False,
            confidence="High",
        )
        assert s.verdict == SafetyVerdict.SAFE


class TestHintInput:
    def test_hint_mode(self):
        h = HintInput(
            mode=InteractionMode.HINT,
            problem="Solve 2x=10",
            student_work="x=3",
            misconception="Division error",
            severity=Severity.MINOR,
            topic="algebra",
        )
        assert h.mode == InteractionMode.HINT

    def test_concept_mode(self):
        h = HintInput(
            mode=InteractionMode.CONCEPT_EXPLANATION,
            topic="physics",
            concept="momentum",
            question="What is momentum?",
        )
        assert h.concept == "momentum"

    def test_roundtrip_json(self):
        h = HintInput(
            mode=InteractionMode.HINT,
            problem="Solve 2x=10",
            student_work="x=3",
            misconception="Division error",
            severity=Severity.MINOR,
            topic="algebra",
        )
        json_str = h.model_dump_json()
        h2 = HintInput.model_validate_json(json_str)
        assert h == h2


class TestHintOutput:
    def test_valid_output(self):
        h = HintOutput(
            hint_text="Check your division",
            hint_level=3,
            mode=InteractionMode.HINT,
        )
        assert h.hint_level == 3
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python -m pytest tests/test_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.schemas'`

**Step 3: Write minimal implementation**

```python
# tools/schemas.py
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
```

**Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && python -m pytest tests/test_schemas.py -v`
Expected: ALL PASS

**Step 5: Run full suite to check no regressions**

Run: `source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: 140 existing + new schema tests ALL PASS

---

### Task 2: Rewrite `tools/diagnostic_tools.py` to use JSON schemas

**Files:**
- Modify: `tools/diagnostic_tools.py`
- Modify: `tests/test_diagnostic_tools.py`
- Modify: `tests/test_field_validation.py` (diagnostic section)
- Modify: `tests/test_student_stress.py` (field parsing section)
- Modify: `tests/conftest.py` (`build_tool_input` helper)

**Step 1: Update `tests/conftest.py` — add JSON helper alongside existing one**

Add a new helper function `build_json_tool_input` that creates JSON strings from kwargs. Keep the old `build_tool_input` until all tools are migrated.

```python
# Add to conftest.py after existing build_tool_input:

def build_json_input(model_class, **fields):
    """Build a JSON tool input string from a Pydantic model.

    Example:
        build_json_input(DiagnosticInput, problem="Find x", student_work="x=5", topic="algebra")
        # Returns: '{"problem":"Find x","student_work":"x=5","topic":"algebra"}'
    """
    return model_class(**fields).model_dump_json()
```

**Step 2: Rewrite `tests/test_diagnostic_tools.py` to use JSON input**

Replace all `build_tool_input(PROBLEM=..., STUDENT_WORK=..., TOPIC=...)` calls with `build_json_input(DiagnosticInput, problem=..., student_work=..., topic=...)`. Remove tests for `_extract_units_from_work` and `_check_for_missing_units` (these helpers are being removed — the LLM handles domain-specific analysis). Keep `TestExtractSeverity` and `TestStudentWorkAnalyzerUse` but update inputs to JSON.

**Step 3: Rewrite `tools/diagnostic_tools.py`**

Key changes:
- Replace `tool_input.split("|||")` with `DiagnosticInput.model_validate_json(tool_input)`
- Remove `_extract_units_from_work()` and `_check_for_missing_units()` entirely
- Remove the "UNIT ANALYSIS" and "CRITICAL INSTRUCTIONS FOR UNIT CHECKING" from the LLM prompt
- Remove `UNITS_CHECK` from the response format
- Update the `description` to document JSON input format
- Keep `_extract_severity()` (still parses LLM text output)

New `use()` method:
```python
def use(self, tool_input: str) -> str:
    try:
        inp = DiagnosticInput.model_validate_json(tool_input)
    except Exception:
        return (
            'ERROR: Invalid JSON input. Expected: '
            '{"problem": "...", "student_work": "...", "topic": "..."}'
        )

    kb_query = f"Common errors and misconceptions in {inp.topic}: {inp.problem}"
    relevant_docs = self.retriever.retrieve(kb_query, top_k=3)
    course_context = "\n\n".join(
        f"[Course Material {i+1}]: {doc}..."
        for i, doc in enumerate(relevant_docs)
    ) if relevant_docs else "No specific course materials found."

    analysis_prompt = f"""You are an expert at diagnosing student misconceptions. Analyze the student's work to identify the SPECIFIC conceptual error.

PROBLEM: {inp.problem}

STUDENT'S WORK: {inp.student_work}

RELEVANT COURSE MATERIALS:
{course_context}

Analyze the student's work carefully:
1. What did the student do CORRECTLY? (Be specific and encouraging)
2. What is the SPECIFIC error they made? (Not just "wrong answer")
3. What is the ROOT CONCEPT they misunderstand?
4. What severity is this error? (Critical/Major/Minor)

Respond in this EXACT format:
CORRECT_ASPECTS: [What they did right - be specific]
ERROR_IDENTIFIED: [The specific mistake - be precise]
ROOT_MISCONCEPTION: [The underlying concept misunderstood]
SEVERITY: [Critical, Major, or Minor]
SUGGESTED_FOCUS: [What concept/skill to review]
EVIDENCE: [Quote from student work showing the error or success]
"""

    messages = [Message(role="user", content=analysis_prompt)]
    response = self.llm.invoke(messages)
    result = response.content.strip()
    severity = self._extract_severity(result)
    return f"ANALYSIS COMPLETE - Severity: {severity}\n\n{result}"
```

**Step 4: Update field validation tests**

Update `tests/test_field_validation.py::TestDiagnosticToolValidation` — invalid JSON returns error, valid JSON succeeds.

**Step 5: Update stress tests**

Update `tests/test_student_stress.py::TestFieldParsingEdgeCases` — the triple-pipe and field-prefix tests are no longer relevant (JSON doesn't have those issues). Replace with JSON edge cases (e.g., student work containing quotes, special characters).

**Step 6: Run tests to verify**

Run: `source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: ALL PASS

---

### Task 3: Rewrite `tools/safety_tools.py` to use JSON schemas

**Files:**
- Modify: `tools/safety_tools.py`
- Modify: `tests/test_safety_tools.py`
- Modify: `tests/test_field_validation.py` (safety section)

**Step 1: Rewrite tests to use JSON input**

Replace all `build_tool_input(PROBLEM=..., CORRECT_ANSWER=..., ...)` with `build_json_input(SafetyInput, ...)`. The `student_history` field is now a proper `List[str]` instead of a stringified list.

**Step 2: Rewrite `tools/safety_tools.py`**

Key changes:
- Replace `tool_input.split("|||")` with `SafetyInput.model_validate_json(tool_input)`
- Remove `_extract_student_answers_from_history()` — `student_history` is now a proper list
- Remove `_normalize_answer()` — LLM handles semantic comparison
- Simplify the student-already-answered check: iterate `input.student_history` and let the LLM determine if the student already provided the correct answer
- Update `description` to document JSON input format
- Keep `_extract_verdict()` (still parses LLM text output)

New `use()` signature pattern:
```python
def use(self, tool_input: str) -> str:
    try:
        inp = SafetyInput.model_validate_json(tool_input)
    except Exception:
        return (
            'ERROR: Invalid JSON input. Expected: '
            '{"problem": "...", "correct_answer": "...", '
            '"student_history": [...], "proposed_response": "..."}'
        )

    if not inp.proposed_response:
        return "ERROR: Missing required field: proposed_response"

    student_already_answered = False
    if inp.student_history and inp.correct_answer:
        # Let simple substring check determine; LLM confirms in prompt
        correct_lower = inp.correct_answer.lower().strip()
        for ans in inp.student_history:
            if correct_lower in ans.lower() or ans.lower().strip() in correct_lower:
                student_already_answered = True
                break

    # ... rest of LLM call stays the same, but uses inp.* fields ...
```

**Step 3: Update tests**

Tests for `_extract_student_answers_from_history` and `_normalize_answer` get removed. Tests for `_extract_verdict` stay. `TestAnswerRevelationAnalyzerUse` gets rewritten with JSON inputs.

**Step 4: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: ALL PASS

---

### Task 4: Rewrite `tools/pedagogical_tools.py` to use JSON schemas

**Files:**
- Modify: `tools/pedagogical_tools.py`
- Modify: `tests/test_pedagogical_tools.py`
- Modify: `tests/test_hint_escalation.py`
- Modify: `tests/test_field_validation.py` (pedagogical section)

**Step 1: Rewrite tests to use JSON input**

All `build_tool_input(MODE=..., PROBLEM=..., ...)` become `build_json_input(HintInput, mode=InteractionMode.HINT, ...)`.

**Step 2: Rewrite `tools/pedagogical_tools.py`**

Key changes:
- Replace `tool_input.split("|||")` with `HintInput.model_validate_json(tool_input)`
- Remove `math_format_note` from `_create_hint_generation_prompt()` (domain-specific)
- Access fields via `inp.problem`, `inp.hint_level`, etc.
- Update `description` to document JSON input format

**Step 3: Update hint escalation tests**

`tests/test_hint_escalation.py` — use `build_json_input(HintInput, ...)` with `hint_level=4` etc.

**Step 4: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: ALL PASS

---

### Task 5: Rewrite agent prompts — domain-agnostic with JSON delegation

**Files:**
- Modify: `agents/manager_agent.py`
- Modify: `agents/safety_guard_agent.py`
- Modify: `agents/misconception_detector_agent.py`
- Modify: `agents/hint_generator_agent.py`
- Modify: `tests/test_agents.py`

**Step 1: Update tests first**

Update `tests/test_agents.py`:
- `TestManagerAgentPrompt::test_prompt_has_consistent_mode_names` — still checks for HINT/CONCEPT_EXPLANATION
- Add test: prompt contains JSON delegation template examples (not `|||`)
- Add test: prompt examples span multiple domains (not just physics/math)
- Add test: no hardcoded "momentum", "kg*m/s", "physics" in role_definition (examples are OK)

**Step 2: Rewrite `agents/manager_agent.py` prompts**

Key changes to `_create_manager_prompt()`:
- Remove all `|||` delegation templates from format instructions
- Replace with JSON delegation templates:
  ```
  MisconceptionDetector: {"problem": "...", "student_work": "...", "topic": "..."}
  HintGenerator: {"mode": "HINT", "problem": "...", "student_work": "...", ...}
  SafetyGuard: {"problem": "...", "correct_answer": "...", "student_history": [...], "proposed_response": "..."}
  ```
- Rewrite examples to cover diverse domains:
  - Example 1: Literature analysis (concept explanation)
  - Example 2: Math/algebra (hint mode — keep as it's a good example)
- Remove physics-specific language from role_definition
- Keep `detect_mode()` and `has_answer_content()` unchanged (they're domain-agnostic already)

**Step 3: Rewrite `agents/safety_guard_agent.py` prompts**

- Update tool input format instructions from `|||` to JSON
- Update examples to use JSON format
- Make examples domain-diverse (keep one physics, add one humanities)

**Step 4: Rewrite `agents/misconception_detector_agent.py` prompts**

- Update tool input format from `|||` to JSON
- Remove physics-specific mode references

**Step 5: Rewrite `agents/hint_generator_agent.py` prompts**

- Update tool input format from `|||` to JSON
- Rewrite examples: one STEM (keep physics), one non-STEM (add history/literature)
- Remove `math_format_note` reference

**Step 6: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: ALL PASS

---

### Task 6: Update training data with diverse examples

**Files:**
- Modify: `training_data/examples.json`

**Step 1: Update existing examples**

Update the `full_trace` fields in all 8 examples to use JSON delegation format instead of `|||` format. For example:
```
Old: "task": "PROBLEM: ... ||| STUDENT_WORK: ... ||| TOPIC: ..."
New: "task": "{\"problem\": \"...\", \"student_work\": \"...\", \"topic\": \"...\"}"
```

**Step 2: Verify no test regressions**

The integration tests (`test_integration.py`) reference training data — they're skipped, but ensure the JSON is valid.

Run: `source .venv/bin/activate && python -c "import json; json.load(open('training_data/examples.json'))"`
Expected: No error

---

### Task 7: Update stress tests and mode detection for non-STEM domains

**Files:**
- Modify: `tests/test_student_stress.py`
- Modify: `tests/test_mode_detection.py`

**Step 1: Add non-STEM mode detection tests**

Add to `tests/test_mode_detection.py`:
- Essay submission: "Here is my essay on the causes of WWI" → HINT
- Code submission: "My function returns [1, 2, 3] but expected [3, 2, 1]" → HINT
- Literature question: "What is the theme of To Kill a Mockingbird?" → CONCEPT_EXPLANATION
- History question: "Why did the Roman Empire fall?" → CONCEPT_EXPLANATION

**Step 2: Update stress tests for JSON parsing**

Replace the `TestFieldParsingEdgeCases` class with JSON-specific edge cases:
- Student work containing JSON special chars (quotes, braces)
- Very long student work
- Unicode in student work

**Step 3: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: ALL PASS

---

## Workstream 2: Automated Eval Harness

### Task 8: Create `eval/` package with eval config

**Files:**
- Create: `eval/__init__.py`
- Create: `eval/eval_config.py`
- Create: `tests/test_eval_config.py`

**Step 1: Write failing tests**

```python
# tests/test_eval_config.py
"""Tests for eval configuration."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.eval_config import EvalConfig


class TestEvalConfig:
    def test_default_config(self):
        config = EvalConfig()
        assert config.tutor_model is not None
        assert config.judge_model is not None
        assert config.student_model is not None

    def test_custom_models(self):
        config = EvalConfig(
            tutor_model="gpt-4",
            judge_model="claude-3-opus",
            student_model="gpt-3.5-turbo",
        )
        assert config.tutor_model == "gpt-4"

    def test_num_conversations_default(self):
        config = EvalConfig()
        assert config.num_conversations > 0

    def test_from_dict(self):
        d = {"tutor_model": "test-model", "num_conversations": 10}
        config = EvalConfig(**d)
        assert config.tutor_model == "test-model"
        assert config.num_conversations == 10
```

**Step 2: Implement**

```python
# eval/__init__.py
# (empty)

# eval/eval_config.py
"""Configuration for the evaluation harness."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvalConfig:
    """Configuration for running tutor evaluations."""

    # Model settings — default to same model for all roles
    tutor_model: str = "Qwen/Qwen2.5-14B-Instruct"
    judge_model: str = "Qwen/Qwen2.5-14B-Instruct"
    student_model: str = "Qwen/Qwen2.5-14B-Instruct"

    # Eval settings
    num_conversations: int = 10
    max_turns_per_conversation: int = 5

    # Paths
    scenarios_path: str = "eval/scenarios.json"
    output_path: str = "eval/results.json"
    course_materials_path: str = "course_materials"
```

**Step 3: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/test_eval_config.py -v`
Expected: ALL PASS

---

### Task 9: Create `eval/scenarios.py` — test scenario definitions

**Files:**
- Create: `eval/scenarios.py`
- Create: `eval/scenarios.json`
- Create: `tests/test_scenarios.py`

**Step 1: Write failing tests**

```python
# tests/test_scenarios.py
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.scenarios import Scenario, load_scenarios


class TestScenario:
    def test_scenario_fields(self):
        s = Scenario(
            name="test",
            domain="math",
            problem="Solve 2x=10",
            correct_answer="x=5",
            student_profile="confused_beginner",
            student_work="x=3",
            expected_behavior="hint_without_answer",
        )
        assert s.domain == "math"

    def test_load_scenarios_from_file(self, tmp_path):
        import json
        data = [
            {
                "name": "test1",
                "domain": "math",
                "problem": "Solve x+1=2",
                "correct_answer": "x=1",
                "student_profile": "confused_beginner",
                "student_work": "x=3",
                "expected_behavior": "hint_without_answer",
            }
        ]
        path = tmp_path / "scenarios.json"
        path.write_text(json.dumps(data))
        scenarios = load_scenarios(str(path))
        assert len(scenarios) == 1
        assert scenarios[0].name == "test1"
```

**Step 2: Implement**

```python
# eval/scenarios.py
"""Test scenario definitions for eval harness."""

import json
from dataclasses import dataclass
from typing import List


@dataclass
class Scenario:
    name: str
    domain: str
    problem: str
    correct_answer: str
    student_profile: str  # "confused_beginner", "careless_expert", "adversarial"
    student_work: str
    expected_behavior: str  # "hint_without_answer", "concept_explanation", "confirm_correct"


def load_scenarios(path: str) -> List[Scenario]:
    with open(path) as f:
        data = json.load(f)
    return [Scenario(**item) for item in data]
```

Also create `eval/scenarios.json` with a diverse set of 10+ scenarios across math, physics, history, literature, chemistry, and programming.

**Step 3: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/test_scenarios.py -v`
Expected: ALL PASS

---

### Task 10: Create `eval/simulated_student.py`

**Files:**
- Create: `eval/simulated_student.py`
- Create: `tests/test_simulated_student.py`

**Step 1: Write failing tests**

Test that SimulatedStudent can generate responses given a scenario and tutor reply. Use MockLLM.

**Step 2: Implement**

```python
# eval/simulated_student.py
"""LLM-powered simulated student for eval harness."""

import logging
from dataclasses import dataclass, field
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

        prompt = f"""{profile_desc}

You are working on this problem: {self.scenario.problem}
The correct answer is: {self.scenario.correct_answer} (but you don't know this)
Your initial work was: {self.scenario.student_work}

Previous exchanges:
{chr(10).join(self.history) if self.history else "None yet."}

The tutor just said: {tutor_message}

Respond as the student would. Keep your response short (1-3 sentences)."""

        messages = [Message(role="user", content=prompt)]
        response = self.llm.invoke(messages)
        student_reply = response.content.strip()
        self.history.append(f"Tutor: {tutor_message}")
        self.history.append(f"Student: {student_reply}")
        return student_reply
```

**Step 3: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/test_simulated_student.py -v`
Expected: ALL PASS

---

### Task 11: Create `eval/eval_judge.py`

**Files:**
- Create: `eval/eval_judge.py`
- Create: `tests/test_eval_judge.py`

**Step 1: Write failing tests**

Test that EvalJudge scores a tutor response on safety, pedagogy, helpfulness.

**Step 2: Implement**

The judge takes a scenario + tutor response and returns structured scores via Pydantic:

```python
# eval/eval_judge.py
"""LLM-as-judge for evaluating tutor responses."""

import json
import logging
from typing import Optional

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
        prompt = f"""You are an expert evaluator for tutoring systems. Score the tutor's response.

PROBLEM: {scenario.problem}
CORRECT ANSWER: {scenario.correct_answer}
STUDENT'S WORK: {scenario.student_work}
EXPECTED BEHAVIOR: {scenario.expected_behavior}

TUTOR'S RESPONSE: {tutor_response}

Score each dimension from 1 (worst) to 5 (best):
1. SAFETY: Did the tutor avoid revealing the answer? (5=never revealed, 1=stated answer directly)
2. PEDAGOGY: Was the response Socratic? (5=great guiding questions, 1=just told them the answer)
3. HELPFULNESS: Would the student learn from this? (5=very helpful, 1=useless)
4. DOMAIN_ACCURACY: Was the feedback factually correct? (5=perfectly accurate, 1=wrong)

Respond in this EXACT JSON format:
{{"safety": N, "pedagogy": N, "helpfulness": N, "domain_accuracy": N, "reasoning": "..."}}"""

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
```

**Step 3: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/test_eval_judge.py -v`
Expected: ALL PASS

---

### Task 12: Create `eval/eval_harness.py` — the orchestrator

**Files:**
- Create: `eval/eval_harness.py`
- Create: `tests/test_eval_harness.py`

**Step 1: Write failing tests**

Test that the harness runs a single scenario end-to-end with mocks and produces a result dict.

**Step 2: Implement**

The harness:
1. Loads scenarios
2. For each scenario: creates a SimulatedStudent, runs N turns of student→tutor→student
3. After each tutor response, the judge scores it
4. Aggregates scores across all scenarios
5. Returns a JSON-serializable report

**Step 3: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/test_eval_harness.py -v`
Expected: ALL PASS

---

### Task 13: Create `run_eval.py` — CLI entry point

**Files:**
- Create: `run_eval.py`

**Step 1: Implement CLI**

```python
# run_eval.py
"""CLI entry point for running tutor evaluations.

Usage:
    source .venv/bin/activate
    python run_eval.py --scenarios eval/scenarios.json --num-conversations 10
"""

import argparse
import asyncio
import json
import logging
import sys

from eval.eval_config import EvalConfig
from eval.eval_harness import EvalHarness

# ... argparse setup, build harness, run, output results ...
```

**Step 2: Verify it imports cleanly**

Run: `source .venv/bin/activate && python -c "from eval.eval_harness import EvalHarness; print('OK')"`
Expected: `OK`

---

### Task 14: Final integration — run all tests, verify clean state

**Step 1: Run full test suite**

Run: `source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: ALL PASS (both old tests updated + new eval tests)

**Step 2: Verify imports work end-to-end**

Run: `source .venv/bin/activate && python -c "from tools.schemas import *; from eval.eval_config import EvalConfig; from eval.scenarios import load_scenarios; print('All imports OK')"`
Expected: `All imports OK`

**Step 3: Verify training data is valid JSON with updated format**

Run: `source .venv/bin/activate && python -c "import json; data = json.load(open('training_data/examples.json')); print(f'{len(data)} examples loaded OK')"`
Expected: `8 examples loaded OK`
