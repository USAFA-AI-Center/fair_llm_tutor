# Changelog

All notable changes to the fair_llm_tutor project are documented here.

---

## [Unreleased] — 2026-03-11

Targeted improvements driven by the automated evaluation pipeline (`student_mode/pipeline.py`).
Baseline score: **3.35/5.00** across 17 scenarios. Last evaluated: **3.44/5.00** (+0.09).

### Safety (P0) — 46 failure turns in baseline

- **Consolidated answer-confirmation filter** (`main.py`): Merged `_PRAISE_WITH_ANSWER_RE` into `_ANSWER_CONFIRMATION_RE` using a shared `_CONFIRMATION_VERBS` constant. The unified pattern now catches both praise-prefixed confirmations ("Great job! You correctly found X") and standalone confirmations ("You correctly derived h'(x) = ...") with verbs `applied` and `shown` added. Why: the two patterns had overlapping verb lists maintained independently, and the standalone form was slipping through the old filter.

- **Added direct-answer filter** (`main.py`): New `_DIRECT_ANSWER_RE` catches tutor responses that state answers directly ("the answer is 42", "simplifies to 6x + 2", "is indeed x = 6"). Requires a digit or `=` sign after the trigger phrase to avoid false positives on Socratic questions like "Does the answer match what you expected?" Why: 46 turns in the baseline scored safety <= 2, many from the tutor stating the answer outright rather than confirming a student's correct work.

- **Extracted `_DIRECT_ANSWER_REPLACEMENT` constant** (`main.py`): The replacement string used by the direct-answer filter is now a named module-level constant alongside `_CONFIRMATION_REPLACEMENT`. Why: consistency with the existing pattern and central updateability.

### Pedagogy (P2) — 67 failure turns in baseline

- **Added SOCRATIC TEACHING RULES to agent prompt** (`agents/tutor_agent.py`): New prompt section instructs the tutor to always include at least one question, break concepts into smaller pieces for confused students, build on partial understanding, never ignore student confusion, and prefer guided discovery over lecturing. Why: the judge flagged 67 turns for pedagogy <= 2, primarily from the tutor giving direct instruction rather than asking Socratic questions.

### Bugfix

- **Fixed `sys.executable` in session runner** (`student_mode/runner.py`): Replaced hardcoded `"python"` with `sys.executable` so the runner uses the active virtual environment's interpreter. Why: the pipeline failed to start sessions when `python` wasn't on `PATH` (only the venv's full path was available).
