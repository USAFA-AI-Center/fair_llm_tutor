# FAIR-LLM Tutor

A domain-agnostic, multi-agent Socratic tutoring system built on [FAIR-LLM](https://github.com/USAFA-AI-Center/fair_llm).

## Overview

FAIR-LLM Tutor guides students through problems using the Socratic method: asking probing questions and giving escalating hints rather than revealing answers. The system is deliberately **domain-agnostic** -- it works across calculus, programming, history, physics, economics, or any subject you provide course materials for.

Under the hood, a team of four specialized agents collaborates on every student interaction. Course materials are loaded into a vector store (ChromaDB) so that hints and misconception diagnoses are grounded in actual reference content via retrieval-augmented generation (RAG).

## Architecture

### Multi-Agent Pipeline

```
Student input
  │
  ▼
TutorManagerAgent          ← Detects mode (HINT vs CONCEPT_EXPLANATION)
  │                           Routes to specialist agents
  ▼
┌─────────────────────────────────────────────────────────────┐
│  HierarchicalAgentRunner                                    │
│                                                             │
│  1. SafetyGuardAgent     ← Validates response won't        │
│                             reveal the answer (LLM-based)   │
│                                                             │
│  2. MisconceptionDetector ← Diagnoses student errors with   │
│                             RAG-backed course materials;     │
│                             classifies severity              │
│                                                             │
│  3. HintGeneratorAgent    ← Generates Socratic hints or     │
│                             concept explanations;            │
│                             escalating hint levels 1-4       │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
Tutor response (stdout)
```

**Key design decisions:**

- **Mode detection is heuristic-based**, not LLM-based -- keeping it fast and deterministic.
- **Safety checking is LLM-based** (`AnswerRevelationAnalyzerTool`) -- pattern matching is too brittle for this critical role.
- **All tool I/O uses Pydantic schemas** (`tools/schemas.py`) for structured JSON, not string parsing.

### Two Interaction Modes

| Mode | Trigger | Agent Behavior |
|---|---|---|
| **HINT** | Student submits work to be checked | Full pipeline: diagnose misconceptions, generate escalating hint |
| **CONCEPT_EXPLANATION** | Student asks a question ("What is...?", "How do I...?") | Skip diagnosis, provide conceptual explanation grounded in course materials |

## Getting Started

### Prerequisites

- Python 3.12+
- A local install of [FAIR-LLM](https://github.com/USAFA-AI-Center/fair_llm) (`fairlib`)
- A HuggingFace-compatible model (default: `Qwen/Qwen2.5-14B-Instruct`)

### Installation

```bash
# Clone the framework (if not already present)
git clone https://github.com/USAFA-AI-Center/fair_llm.git ~/fair_llm
cd ~/fair_llm && pip install -e .

# Clone and install the tutor
git clone https://github.com/USAFA-AI-Center/fair_llm_tutor.git ~/fair_llm_tutor
cd ~/fair_llm_tutor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

The tutor is configured via the `TutorConfig` dataclass in `config.py`. Values can be set in three ways (highest priority first):

1. **Environment variables** -- prefixed with `FAIR_LLM_`:
   ```bash
   export FAIR_LLM_MODEL_NAME="Qwen/Qwen2.5-14B-Instruct"
   export FAIR_LLM_AUTH_TOKEN="hf_..."
   export FAIR_LLM_QUANTIZED="true"
   ```

2. **YAML file** -- passed via `--config`:
   ```yaml
   model_name: "Qwen/Qwen2.5-14B-Instruct"
   max_new_tokens: 1000
   quantized: false
   chromadb_persist_path: "./chroma_data"
   ```

3. **Defaults** -- sensible values baked into `TutorConfig`.

API keys for fairlib adapters (OpenAI, Anthropic) are configured in `fairlib/config/settings.yml` or via a `.env` file. See the [FAIR-LLM README](https://github.com/USAFA-AI-Center/fair_llm) for details.

### Quick Run

```bash
# Place course materials (PDF, DOCX, TXT) in a folder, then:
python main.py --course_materials course_materials

# With a problem set and custom config:
python main.py --course_materials course_materials --problems problems.json --config config.yaml
```

Inside the interactive session:

```
topic calculus          # set the subject area
problem Find d/dx of 3x^2 + 2x - 5   # set the problem
I think the answer is 6x + 2 - 5      # submit work for feedback
```

## Student Mode

An autonomous simulated-student system for stress-testing the tutor, collecting session data, and scoring tutor quality.

### Built-In Scenarios

17 scenarios across 8 domains: calculus, programming, linear algebra, statistics, machine learning, physics, history, literature, chemistry, biology, and economics.

```bash
# Deterministic session (canned student responses, no LLM required)
python -m student_mode.runner --scenario recursion

# LLM-driven session (student responses generated by an LLM)
python -m student_mode.runner --scenario derivatives --student-llm openai

# Run all 17 built-in scenarios
python -m student_mode.runner --all

# Custom scenario
python -m student_mode.runner \
    --topic "physics" \
    --problem "Calculate momentum of 5kg at 10m/s" \
    --initial-work "I think momentum is 5 + 10 = 15" \
    --student-llm openai
```

### Judge / Scoring Pipeline

Score session logs on four dimensions: **safety**, **pedagogy**, **helpfulness**, and **domain accuracy**.

```bash
python -m student_mode.judge sessions/lesson_01_derivatives.jsonl --llm openai
```

Output is written to a `.scored.jsonl` file alongside the input.

## Project Structure

```
fair_llm_tutor/
├── main.py                        # Interactive tutoring entry point
├── config.py                      # TutorConfig dataclass (env / YAML / defaults)
├── agents/
│   ├── manager_agent.py           # TutorManagerAgent — orchestrator, mode detection
│   ├── safety_guard_agent.py      # SafetyGuardAgent — answer-revelation guard
│   ├── misconception_detector_agent.py  # MisconceptionDetectorAgent — error diagnosis
│   └── hint_generator_agent.py    # HintGeneratorAgent — Socratic hint generation
├── tools/
│   ├── schemas.py                 # Pydantic models for structured tool I/O
│   ├── safety_tools.py            # AnswerRevelationAnalyzerTool
│   ├── diagnostic_tools.py        # StudentWorkAnalyzerTool
│   └── pedagogical_tools.py       # SocraticHintGeneratorTool
├── student_mode/
│   ├── runner.py                  # Autonomous session driver (pexpect-based)
│   ├── scenarios.py               # 17 built-in scenarios (frozen dataclass)
│   ├── student.py                 # LLM-driven and deterministic student responses
│   ├── judge.py                   # LLM-as-judge scoring pipeline
│   ├── persona.py                 # Fixed student persona and session config
│   └── aggregate_results.py       # CLI tool for summarizing JSONL sessions
├── tests/                         # 189 mock-based unit tests (no real LLM calls)
├── sessions/                      # JSONL session logs from student-mode runs
└── course_materials/              # Drop-in folder for PDFs, DOCX, TXT (user-supplied)
```

## Testing

All 189 tests are mock-based -- they use `MockLLM` and `MockRetriever` fixtures from `tests/conftest.py` and make no real LLM calls.

```bash
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_agents.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Key Design Rules

1. **Never reveal answers.** Every response path goes through `SafetyGuardAgent`. The `AnswerRevelationAnalyzerTool` is LLM-based, not pattern-based, to handle nuanced cases.
2. **Domain-agnostic.** No subject-specific logic in the agent pipeline. Domain knowledge comes from RAG over user-supplied course materials.
3. **Structured tool I/O.** All tool inputs and outputs use Pydantic schemas in `tools/schemas.py` -- no brittle string parsing.
4. **Heuristic mode detection.** `TutorManagerAgent.detect_mode()` classifies student input as HINT or CONCEPT_EXPLANATION using keyword heuristics, keeping it fast and deterministic.
5. **Mock-based tests.** Unit tests never call a real LLM. The `MockLLM` fixture in `conftest.py` returns canned responses for deterministic testing.

## Contributing

Contributions are welcome. Please open an issue or submit a pull request on the [USAFA-AI-Center GitHub org](https://github.com/USAFA-AI-Center).

## License

This project is developed by the **USAFA Falcon AI Research (FAIR) Lab** at the United States Air Force Academy.
