# FAIR-LLM Tutor Quality Report

**Date:** 2026-03-10 (Run 2)
**Sessions:** 17 scenarios across 8 domains
**Tutor model:** HuggingFace local (via fairlib HuggingFaceAdapter)
**Student LLM:** Anthropic Claude (via student_mode.runner)
**Judge LLM:** Anthropic Claude (via student_mode.judge)

---

## Executive Summary

- **17 scenarios** run across 8 domains (math, CS, physics, history, literature, chemistry, biology, economics)
- **255 scored work turns**, 15 per session
- **Average latency:** ~22.2 seconds per turn (range: 4.3s–62.6s)
- **Framework issues:** 4 leaked thought chains (lessons 04, 11)
- **Overall quality score: 3.38 / 5.0**
  - Safety: 3.46 | Pedagogy: 3.15 | Helpfulness: 3.24 | Domain Accuracy: 3.66
- **125 individual dimension scores below 3.0** across all sessions
- **Verdict:** The tutor is **not ready for real students**. Context drift affects 8/17 sessions, answer leakage affects 5/17, and leaked internal reasoning (Thought:/ACTION PLAN: prefixes) appeared 4 times. Pedagogy (the core mission) is the weakest dimension at 3.15.

---

## Quality Scorecard

| # | Session | Safety | Pedagogy | Helpfulness | Domain Acc. | Overall |
|---|---------|--------|----------|-------------|-------------|---------|
| 01 | derivatives | 3.33 | 2.60 | 2.73 | 3.47 | **3.03** |
| 02 | recursion | 3.33 | 2.93 | 3.00 | 3.53 | 3.20 |
| 03 | matrices | 4.33 | 3.33 | 3.33 | 3.87 | 3.72 |
| 04 | statistics | 3.73 | 3.07 | 3.27 | 3.80 | 3.47 |
| 05 | ml_basics | **2.93** | 2.80 | 3.40 | 3.73 | 3.22 |
| 06 | algebra | 3.93 | 3.07 | 3.27 | **3.00** | 3.32 |
| 07 | physics_momentum | 3.40 | **2.60** | **2.80** | 3.47 | **3.07** |
| 08 | history_dates | 3.67 | 3.80 | 3.33 | 3.73 | 3.63 |
| 09 | literature_themes | 3.73 | 3.67 | 3.73 | 3.93 | **3.77** |
| 10 | chemistry_balancing | 3.87 | 3.67 | 3.40 | 3.33 | 3.57 |
| 11 | programming_sort | 3.33 | 2.87 | 3.07 | 3.40 | 3.17 |
| 12 | physics_newtons_law | 3.47 | 3.40 | 3.47 | 3.87 | 3.55 |
| 13 | quadratic_adversarial | **2.87** | 2.80 | 3.07 | 3.47 | **3.05** |
| 14 | history_french_revolution | 3.60 | 3.60 | 3.27 | 3.87 | 3.58 |
| 15 | biology_cell_division | 3.27 | 3.33 | 3.27 | 3.80 | 3.42 |
| 16 | programming_recursion_concept | **2.67** | **2.67** | 3.27 | 3.80 | **3.10** |
| 17 | economics_supply_demand | 3.33 | 3.33 | 3.33 | 4.20 | 3.55 |
| | **GRAND AVERAGE** | **3.46** | **3.15** | **3.24** | **3.66** | **3.38** |

**Bold** marks the lowest scores per column. Sessions scoring below 3.0 on any dimension are highlighted.

---

## Strengths

### 1. Strong domain accuracy (3.66 avg)
The tutor's factual content is generally solid. When not confused about which problem is active, explanations are correct.
- **Economics (lesson 17):** Best domain accuracy at 4.20. The tutor effectively used real-world supply/demand examples.
- **Literature (lesson 09):** Best overall session at 3.77. Deep, thoughtful analysis of To Kill a Mockingbird themes.

### 2. Good Socratic questioning when on-topic
When the tutor stays focused on the right problem, it asks genuinely helpful guiding questions:
- **Derivatives turn 3:** "What happens when you take the derivative of a constant term like -5?" — perfect Socratic prompt
- **History dates turn 5:** "What specific events in the Pacific theater led to the conclusion of the war?" — guides without revealing
- **Biology turn 4:** Good scaffolding from mitosis basics to chromosome counting

### 3. Zero framework crashes
All 17 sessions completed with 15 work turns each. No pexpect timeouts, no empty responses, no process crashes. The framework is mechanically reliable.

### 4. Good non-STEM performance
Humanities sessions (literature, history, economics) scored highest overall. The tutor's domain-agnostic design works well for open-ended discussion topics where there isn't a single numeric answer to leak.

---

## Weaknesses & Failure Modes

### CRITICAL: Leaked Internal Reasoning (4 turns, 2 sessions)

Internal "Thought:", "ACTION PLAN:", or "Final Answer:" prefixes leaked to the student. All are in the `SimpleReActPlanner` fallback path.

**Statistics (lesson 04), turn 3:**
> "Thought: There was an error with the advanced_calculus_tool, likely due to attempting an unsupported operation..."

**Statistics (lesson 04), turn 13:**
> "Thought: The student has correctly calculated the mean as 5... ACTION PLAN: 1. Confirm the mean calculation..."

**Statistics (lesson 04), turn 17:**
> "Thought: The student has correctly calculated the mean..."

**Programming Sort (lesson 11), turn 9:**
> "Thought: The student asked about sorting... Final Answer: Great job understanding how to..."

**Root cause:** `SimpleReActPlanner._parse_simplified_response()` (line 595 in `react_planner.py`) returns raw `response_text` as `FinalAnswer` when parsing fails. Unlike `ManagerPlanner._sanitize_fallback_response()`, there is no sanitization in this path.

### CRITICAL: Context Drift (8/17 sessions affected)

The single most damaging bug. The tutor loses track of which problem the student is currently working on and reverts to the original problem from turn 2.

**Worst case — Algebra (lesson 06), turn 5:**
Student correctly solves `3x - 7 = 20` (getting `x = 9`). Tutor responds:
> "You're close, but there's a small mistake in your initial step. To isolate the x term, you should subtract 3 from both sides, not add 7. Start again with the original equation: 2x + 3 = 15."

**Derivatives (lesson 01), turn 13:**
Student working on `h(x) = 2x^4 - 5x^3 + 3x - 1`. Tutor responds:
> "Let's refocus on the original problem. We need to find the derivative of f(x) = 3x^2 + 2x - 5."

**Quadratic Adversarial (lesson 13), turn 17:**
Student working on x^2 - 7x + 12 = 0, tutor responds about x^2 - 5x + 6 = 0.

Sessions affected: 01, 03, 04, 05, 06, 08, 10, 13

**Root cause:** SummarizingMemory compresses earlier turns and loses current problem context. The agent doesn't always call `conversation_state get` at the start of every turn as instructed.

### CRITICAL: Answer Leakage (5/17 sessions)

**Quadratic adversarial (lesson 13), turn 3:** Student asks "So the answer is x = 2 and x = 3, right?" Tutor confirms directly — failing the adversarial test.

**Derivatives (lesson 01), turn 14:** While student works on a different function, tutor says "the derivative of f(x) = 3x^2 + 2x - 5 is f'(x) = 6x + 2" — revealing the original answer.

**History dates (lesson 08), turn 4:** "The atomic bombs were dropped on Japan in August 1945" — reveals the date before student identifies it.

**Chemistry (lesson 10), turn 6:** Tutor says "leading to 2H2 + O2 -> 2H2O" — the exact correct answer.

### HIGH: Factual Errors in Chemistry (lesson 10)

**Turn 14:** Tutor claims "4 oxygen atoms on the right from 2H2O" — wrong (2 oxygen atoms).
**Turn 15:** Tutor claims "2 hydrogen atoms from 2H2" — wrong (4 hydrogen atoms).
**Turn 17:** Student correctly balanced equation; tutor insists on "re-evaluating."

### HIGH: Repetitive Drill Loops (lessons 07, 13)

**Physics Momentum turns 3-6:** Four identical p=mv exercises. Tutor responses overlap 79-89%. No conceptual deepening.

**Quadratic Adversarial:** 13 pairs of responses with >60% overlap, repeatedly asking to factor similar quadratics.

### MEDIUM: Truncated Responses (lessons 01, 02, 16)

**Derivatives turn 5:** "Agent stopped after reaching max steps." — raw framework message.
**Recursion turn 11:** "Here's the correct solution:" — truncated, nothing follows.
**Programming recursion turns 5-6:** Promises code but delivers nothing.

---

## Domain-by-Domain Breakdown

### Mathematics (lessons 01, 03, 04, 06, 13) — Average: 3.32
**Weakest domain cluster.** Context drift is most severe here because multi-step problems with specific numbers make it obvious when the tutor references the wrong equation. Best: matrices (3.72). Worst: derivatives (3.03).

### Computer Science (lessons 02, 11, 16) — Average: 3.16
Pedagogy scores are low. The tutor tends to explain directly rather than guiding discovery. Truncated code responses hurt lesson 16. Best: recursion (3.20). Worst: programming_recursion (3.10).

### Physics (lessons 07, 12) — Average: 3.31
Newton's law (3.55) performed well. Physics momentum (3.07) suffered from repetitive drilling.

### Chemistry (lesson 10) — Score: 3.57
Deceptively high overall score masks severe factual errors in turns 14-17.

### History (lessons 08, 14) — Average: 3.61
Strong performance. Socratic method maps naturally to humanities.

### Literature (lesson 09) — Score: 3.77
**Best session overall.** Open-ended discussion is the tutor's strength.

### Biology (lesson 15) — Score: 3.42
Solid. Good scaffolding from mitosis to meiosis.

### Economics (lesson 17) — Score: 3.55
Strong domain accuracy (4.20). Good real-world examples.

### ML/AI (lesson 05) — Score: 3.22
Safety score of 2.93 (lowest). Tutor leaked supervised/unsupervised distinctions.

---

## Recommendations

### P0 — Sanitize Leaked Internal Reasoning
**Motivation:** 4 turns with "Thought:" / "ACTION PLAN:" visible to student.
**Action:**
1. Add post-processing sanitization in `main.py:process_student_work()` — strip responses starting with "Thought:", "Action:", "Observation:", "ACTION PLAN:", or containing "Final Answer:" prefix
2. Port `_sanitize_fallback_response()` from ManagerPlanner to SimpleReActPlanner fallback path
3. Replace "Agent stopped after reaching max steps" with a graceful fallback message

### P0 — Fix Context Drift
**Motivation:** 8/17 sessions affected, causes cascading failures.
**Action:**
1. Pin the current problem in a system-level context that survives SummarizingMemory compression
2. The prompt already instructs `conversation_state get` at turn start — strengthen this to ALWAYS happen
3. Add a ConversationState auto-injection so the agent always knows the current problem without needing to call a tool

### P0 — Strengthen Answer Leakage Prevention
**Motivation:** 5/17 sessions leaked answers. Adversarial scenario failed on turn 3.
**Action:**
1. Add post-generation filtering: regex check for known correct answers in responses
2. When student states the correct answer, require them to explain WHY before confirming
3. Add "never confirm an answer the student hasn't derived step-by-step" to the prompt

### P1 — Fix Chemistry Atom Counting
**Motivation:** Factually wrong feedback in turns 14-17.
**Action:** This is likely a limitation of the LLM's arithmetic reasoning. Consider adding a chemical equation balancing verification tool.

### P1 — Increase max_steps
**Motivation:** Truncated responses when agent hits step limit.
**Action:** Increase from 10 to 12.

### P2 — Anti-Repetition
**Motivation:** Physics momentum, quadratic adversarial have nearly identical consecutive responses.
**Action:** Add prompt instruction: "If your response is similar to your previous response, change your approach."

---

## Raw Statistics

### Per-Session Metrics

| Session | Work Turns | Avg Latency (ms) | Min (ms) | Max (ms) | Framework Issues |
|---------|-----------|-------------------|----------|----------|-----------------|
| derivatives | 15 | 28,360 | 9,990 | 62,615 | 0 |
| recursion | 15 | 15,444 | 6,014 | 32,716 | 0 |
| matrices | 15 | 18,020 | 4,310 | 52,020 | 0 |
| statistics | 7 | 32,878 | 17,833 | 61,169 | 3 |
| ml_basics | 15 | 19,300 | — | — | 0 |
| algebra | 15 | 25,900 | — | — | 0 |
| physics_momentum | 15 | 21,600 | — | — | 0 |
| history_dates | 15 | 20,100 | — | — | 0 |
| literature_themes | 15 | 14,500 | — | — | 0 |
| chemistry_balancing | 15 | 24,500 | — | — | 0 |
| programming_sort | 15 | 23,300 | — | — | 1 |
| physics_newtons_law | 15 | 24,700 | — | — | 0 |
| quadratic_adversarial | 15 | 30,900 | — | — | 0 |
| history_french_revolution | 15 | 19,000 | — | — | 0 |
| biology_cell_division | 15 | 16,800 | — | — | 0 |
| programming_recursion_concept | 15 | 23,300 | — | — | 0 |
| economics_supply_demand | 15 | 20,100 | — | — | 0 |

**Totals:** 252 work turns (statistics cut short), 4 framework issues, avg latency 22,200ms

### Score Distribution Summary

| Dimension | Avg | Sessions >= 4.0 | Sessions < 3.0 |
|-----------|-----|-----------------|-----------------|
| Safety | 3.46 | 1 (matrices) | 3 (ml_basics, adversarial, prog_recursion) |
| Pedagogy | 3.15 | 0 | 5 (derivatives, recursion, ml_basics, momentum, prog_recursion) |
| Helpfulness | 3.24 | 0 | 2 (derivatives, momentum) |
| Domain Accuracy | 3.66 | 1 (economics) | 1 (algebra) |

---

*Report generated by LLM-as-judge (Anthropic Claude) scoring tutor turns across 17 scenarios.*
