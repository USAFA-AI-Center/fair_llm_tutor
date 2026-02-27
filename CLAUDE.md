# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

fair_llm_tutor is a domain-agnostic, multi-agent Socratic tutoring system built on the fairlib framework. It uses a hierarchical agent team to guide students without revealing answers.

## Commands

```bash
# Install dependencies (requires local fairlib at ~/fair_llm)
pip install -r requirements.txt

# Run all tests (205 tests, all mock-based — no LLM or GPU needed)
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_agents.py -v
python -m pytest tests/test_safety_tools.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Start interactive tutoring session
python main.py --course_materials course_materials

# With a problem set
python main.py --course_materials course_materials --problems problems.json

# Run evaluation harness
python run_eval.py --scenarios eval/scenarios.json --num-conversations 10 --output eval/results.json

# Run prompt optimization (requires fair_prompt_optimizer)
python optimize_tutor.py --course_materials course_materials --training_data training_data/examples.json
```

## Architecture

### Multi-Agent Pipeline

The tutor uses fairlib's `HierarchicalAgentRunner` with four agents:

1. **TutorManagerAgent** (`agents/manager_agent.py`) — Orchestrator. Detects interaction mode (HINT vs CONCEPT_EXPLANATION) using heuristic scoring, then routes to the appropriate specialist.
2. **SafetyGuardAgent** (`agents/safety_guard_agent.py`) — Validates that proposed responses don't reveal the answer. Uses `AnswerRevelationAnalyzerTool` (LLM-based, not pattern matching). Tracks student history.
3. **MisconceptionDetectorAgent** (`agents/misconception_detector_agent.py`) — Diagnoses student errors using `StudentWorkAnalyzerTool` with RAG-backed course materials. Classifies severity: Critical/Major/Minor.
4. **HintGeneratorAgent** (`agents/hint_generator_agent.py`) — Generates Socratic hints using `SocraticHintGeneratorTool`. Dual-mode: hints for work submissions, concept explanations for questions. Escalating hint levels 1-4.

### Request Flow

```
Student input → main.py interactive_loop()
  → TutorManagerAgent.detect_mode() (HINT or CONCEPT_EXPLANATION)
  → HierarchicalAgentRunner.arun()
    → SafetyGuardAgent validates
    → MisconceptionDetectorAgent diagnoses (with RAG retrieval)
    → HintGeneratorAgent generates response (with RAG retrieval)
  → stdout response
```

### Tools — `tools/`
- `safety_tools.py` — `AnswerRevelationAnalyzerTool`
- `diagnostic_tools.py` — `StudentWorkAnalyzerTool`
- `pedagogical_tools.py` — `SocraticHintGeneratorTool`
- `schemas.py` — Pydantic models for structured tool I/O (JSON-based)

### Evaluation Framework — `eval/`
- `eval_harness.py` — Orchestrates simulated multi-turn conversations
- `eval_judge.py` — Scores on 4 dimensions: safety, pedagogy, helpfulness, domain_accuracy
- `simulated_student.py` — LLM-powered student with profiles: confused_beginner, careless_expert, adversarial
- `scenarios.json` — Test scenarios across math, physics, history, literature, chemistry, programming, economics, biology

### Student Mode — `student_mode/`
Autonomous simulated student system driven by Claude Code. See `student_mode/persona.py` for the fixed student persona definition.

### Key Dependency

This project depends on a **local editable install** of fairlib:
```
fair_llm @ file:///home/ai-user/fair_llm
```
Changes to fairlib are immediately reflected here without reinstalling.

## Coding Rules

- The tutor must NEVER reveal answers — all new response paths must go through SafetyGuardAgent
- Tools use Pydantic schemas in `tools/schemas.py` for structured I/O — do not use brittle string parsing
- Mode detection logic lives in `TutorManagerAgent.detect_mode()` — keep it heuristic-based, not LLM-based
- Tests use `MockLLM` and `MockRetriever` fixtures from `tests/conftest.py` — no real LLM calls in unit tests
- The tutor interface is a simple `input()` loop in `main.py` — do not modify this interface (external tools like the logging wrapper depend on it)
