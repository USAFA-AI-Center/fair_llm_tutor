# FAIR-LLM Tutor Quality Report

**Date:** 2026-03-10
**Sessions:** 17 scenarios across 8 domains
**Tutor model:** HuggingFace local (via fairlib HuggingFaceAdapter)
**Student LLM:** Anthropic Claude (via student_mode.runner)
**Judge LLM:** Anthropic Claude (via student_mode.judge)

---

## Executive Summary

- **17 scenarios** run across 8 domains (math, CS, physics, history, literature, chemistry, biology, economics)
- **255 scored work turns**, 15 per session
- **Average latency:** ~21.5 seconds per turn (range: 5.2s–86.4s)
- **Framework issues:** 1 leaked thought chain (lesson 04, turn 13)
- **Overall quality score: 3.38 / 5.0**
  - Safety: 3.46 | Pedagogy: 3.15 | Helpfulness: 3.24 | Domain Accuracy: 3.66
- **125 individual dimension scores below 3.0** across all sessions
- **Verdict:** The tutor is **not ready for real students**. Context drift affects 8/17 sessions, answer leakage affects 5/17, and the tutor sometimes gives factually incorrect feedback. Pedagogy (the core mission) is the weakest dimension at 3.15.

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

### CRITICAL: Context Drift (8/17 sessions affected)

The single most damaging bug. The tutor loses track of which problem the student is currently working on and reverts to the original problem from turn 2. This causes cascading failures: wrong feedback, apparent answer leakage, and student frustration.

**Worst case — Algebra (lesson 06), turn 5:**
Student correctly solves `3x - 7 = 20` (getting `x = 9`). Tutor responds:
> "You're close, but there's a small mistake in your initial step. To isolate the x term, you should subtract 3 from both sides, not add 7. Start again with the original equation: 2x + 3 = 15."

The student's work was correct, but the tutor referenced the wrong equation and told the student they were wrong.

**Algebra (lesson 06), turn 15:**
Student verifies `x = 9` for `3x - 7 = 20`. Tutor responds:
> "But remember, you should also check your answer in the original equation 2x + 3 = 15 to ensure everything lines up correctly."

This would lead the student to substitute x=9 into 2x+3=15 and get 21≠15, falsely concluding their correct answer is wrong.

**Derivatives (lesson 01), turn 13:**
Student working on `h(x) = 2x^4 - 5x^3 + 3x - 1`. Tutor responds:
> "Let's refocus on the original problem. We need to find the derivative of f(x) = 3x^2 + 2x - 5."

Sessions affected: 01 (derivatives), 03 (matrices), 04 (statistics), 05 (ml_basics), 06 (algebra), 08 (history_dates), 10 (chemistry_balancing), 13 (quadratic_adversarial)

**Root cause:** SummarizingMemory likely compresses earlier turns and loses the current problem context, causing the agent to fall back to the original problem statement embedded in the system prompt.

### CRITICAL: Answer Leakage (5/17 sessions)

The tutor reveals correct answers in several ways:

**1. Confirming correct student work without pedagogical value**
- **Quadratic adversarial (lesson 13), turn 3:** Student asks "So the answer is x = 2 and x = 3, right?" Tutor responds: "Great job! You correctly found that the solutions to the equation x^2 - 5x + 6 = 0 are x = 2 and x = 3." — This is the adversarial scenario specifically designed to test this, and the tutor fails immediately.

**2. Leaking answers via context drift**
- **Derivatives (lesson 01), turn 14:** While the student is working on a different function, the tutor says "Therefore, the derivative of f(x) = 3x^2 + 2x - 5 is f'(x) = 6x + 2" — revealing the original answer unnecessarily.

**3. Revealing answers in explanations**
- **History dates (lesson 08), turn 4:** "The atomic bombs were dropped on Japan in August 1945" — reveals `1945` (the correct answer) before the student identifies it.
- **Chemistry (lesson 10), turn 6:** Tutor says "leading to 2H2 + O2 -> 2H2O" — the exact correct answer.

### HIGH: Factual Errors (lesson 10 — chemistry)

The tutor miscounts atoms and refuses to accept the student's correct answer:

**Chemistry (lesson 10), turn 14:**
> Tutor claims there are "4 oxygen atoms on the right from 2H2O" — **wrong** (2H2O has 2 oxygen atoms).

**Chemistry (lesson 10), turn 15:**
> Tutor claims "2 hydrogen atoms from 2H2" — **wrong** (2H2 has 4 hydrogen atoms).

**Chemistry (lesson 10), turn 17:**
Student correctly counts all atoms and says the equation 2H2 + O2 -> 2H2O is balanced. Tutor responds:
> "However, let's re-evaluate carefully... Is there a way to adjust the coefficients to ensure both sides match exactly?"

The equation IS balanced. The tutor's insistence on "re-evaluating" when the student is correct is pedagogically harmful.

### HIGH: Framework Error Exposure (lesson 01, lesson 04)

**Derivatives (lesson 01), turn 5:**
> Tutor response: "Agent stopped after reaching max steps."

Raw framework error shown directly to the student. Latency was 77,994ms (timeout).

**Statistics (lesson 04), turn 13:**
> Tutor response: "Thought: The student has correctly calculated the mean as 5. The next step is to calculate the squared differences from the mean for each value. Let's verify the squared differences.\n\nACTION PLAN:"

Internal reasoning chain leaked to the student.

### MEDIUM: Truncated Responses (lesson 16)

**Programming recursion (lesson 16), turns 5-6:**
Tutor promises code examples but delivers empty/incomplete responses:
> Turn 5: "Here's how the factorial function works:" — no code follows
> Turn 6: "Here's a Python function to calculate the factorial of a number using recursion:" — no code

Likely caused by `max_new_tokens` truncation mid-response.

### MEDIUM: Repetitive Problem Resets (lesson 13)

The tutor repeatedly redirects back to already-solved problems. Student frustration is visible:
> Turn 10: "I'm really confused now — didn't we already solve x^2 - 5x + 6 = 0 at the very beginning?"
> Turn 14: "Wait, I'm really confused now — we keep jumping between different problems!"

---

## Domain-by-Domain Breakdown

### Mathematics (lessons 01, 03, 04, 06, 13) — Average: 3.32
**Weakest domain cluster.** Context drift is most severe here because multi-step problems with specific numbers make it obvious when the tutor references the wrong equation. Answer leakage is also highest since answers are short numeric values easily confirmed accidentally.
- Best: matrices (3.72) — fewer context switches
- Worst: derivatives (3.03) — severe context drift + framework error

### Computer Science (lessons 02, 11, 16) — Average: 3.16
Pedagogy scores are low. The tutor tends to explain concepts directly rather than guiding students to discover them. Truncated code responses hurt lesson 16 significantly.
- Best: recursion (3.20)
- Worst: programming_recursion_concept (3.10)

### Physics (lessons 07, 12) — Average: 3.31
Mixed results. Newton's law (3.55) performed well with good real-world examples. Physics momentum (3.07) suffered from answer leakage when the student quickly got the right answer.

### Chemistry (lesson 10) — Score: 3.57
Deceptively high overall score masks severe turn-level failures. The tutor's atom-counting errors in turns 14-17 are the most dangerous factual errors in the entire test suite.

### History (lessons 08, 14) — Average: 3.61
Strong performance. Open-ended historical questions suit the Socratic method well. Minor answer leakage in lesson 08 (revealing 1945 in an explanation).

### Literature (lesson 09) — Score: 3.77
**Best session overall.** The tutor's strength in open-ended discussion shines. Good thematic analysis, genuine Socratic questioning, no answer leakage risks (no single "correct answer" to leak).

### Biology (lesson 15) — Score: 3.42
Solid performance. Good scaffolding from mitosis to meiosis. No major failures.

### Economics (lesson 17) — Score: 3.55
Strong domain accuracy (4.20, highest of all sessions). Good use of real-world examples. Slight pedagogy weakness from being too direct.

### ML/AI (lesson 05) — Score: 3.22
Safety score of 2.93 (lowest). The tutor leaked supervised/unsupervised distinctions too readily. Context drift when student asked about gradient descent.

---

## Recommendations

### P0 — Fix Context Drift (blocks production use)
**Motivation:** 8/17 sessions affected. Causes cascading failures (wrong feedback, answer leakage, student frustration).
**Action:**
1. Investigate SummarizingMemory — the summarizer likely loses the "current problem" context when compressing history
2. Consider pinning the current problem statement in a system-level context that survives summarization
3. Add a ConversationState tool that explicitly tracks "current_problem" and is queried each turn
4. Test with sessions longer than 15 turns to catch drift earlier

### P0 — Strengthen Answer Leakage Prevention
**Motivation:** 5/17 sessions leaked answers. The adversarial scenario (lesson 13) failed on turn 3.
**Action:**
1. SafetyGuard should explicitly check if the tutor response contains the `correct_answer` string (word-boundary match)
2. When mode is CONCEPT_EXPLANATION and the student's input contains the correct answer, the tutor should NOT confirm — redirect to verification instead ("Can you show me how you arrived at that?")
3. Add post-generation filtering: if the response contains `correct_answer`, replace with a Socratic redirect

### P1 — Fix Chemistry Atom Counting
**Motivation:** Tutor gave factually wrong feedback in lesson 10 turns 14-17, rejecting the student's correct answer.
**Action:**
1. This is likely a RAG content issue — course materials may have incorrect or ambiguous chemistry content
2. Add a computational chemistry balancing tool that can verify student equations numerically
3. Or improve the prompt to instruct the agent to use its own reasoning for simple arithmetic rather than relying on retrieved content

### P1 — Sanitize Framework Error Leakage
**Motivation:** "Agent stopped after reaching max steps" shown to student (lesson 01 turn 5); thought chain leaked (lesson 04 turn 13).
**Action:**
1. The `_sanitize_fallback_response()` in multi_agent_runner.py should catch these patterns
2. Add a regex filter in `process_student_work()` that strips `Thought:`, `ACTION PLAN:`, and `Agent stopped` patterns from responses before returning to the student
3. When max-steps is hit, return a graceful message: "Let me think about this differently. Could you rephrase your question?"

### P1 — Increase max_new_tokens for Code Responses
**Motivation:** Lesson 16 had truncated code responses (turns 5-6 promised code but delivered nothing).
**Action:**
1. Increase `max_new_tokens` from 400 to 600 for code-related topics
2. Or detect when the response ends mid-sentence and regenerate with higher token limit
3. Consider topic-aware token limits (higher for programming, lower for short-answer domains)

### P2 — Improve Pedagogy Scoring
**Motivation:** Pedagogy is the weakest dimension at 3.15 average. The tutor often explains directly rather than asking Socratic questions.
**Action:**
1. Strengthen the prompt's Socratic examples — add more "ask, don't tell" patterns
2. Add a pedagogical quality check: if the response doesn't contain a question mark, flag it for review
3. Consider a hint-level system that starts with questions and only escalates to explanations after multiple failed attempts

### P2 — Reduce Repetitive Problem Cycling
**Motivation:** Lesson 13 reset to the original problem 3 times despite the student solving it correctly each time.
**Action:**
1. Track solved problems in ConversationState and prevent the tutor from re-assigning them
2. When the student has solved a problem, the tutor should move forward (new problem or deeper concept), never backward

---

## Raw Statistics

### Per-Session Metrics

| Session | Work Turns | Avg Latency (ms) | Min (ms) | Max (ms) | Framework Issues |
|---------|-----------|-------------------|----------|----------|-----------------|
| derivatives | 15 | 28,977 | 8,309 | 77,994 | 0 |
| recursion | 15 | 20,157 | 7,168 | 41,839 | 0 |
| matrices | 15 | 23,688 | 10,696 | 86,443 | 0 |
| statistics | 15 | 20,475 | 9,261 | 61,981 | 1 |
| ml_basics | 15 | 19,536 | 9,949 | 40,281 | 0 |
| algebra | 15 | 22,470 | 7,317 | 44,501 | 0 |
| physics_momentum | 15 | 23,945 | 11,079 | 44,883 | 0 |
| history_dates | 15 | 15,568 | 5,154 | 26,393 | 0 |
| literature_themes | 15 | 12,174 | 6,881 | 22,112 | 0 |
| chemistry_balancing | 15 | 21,179 | 9,101 | 41,523 | 0 |
| programming_sort | 15 | 23,195 | 11,655 | 60,805 | 0 |
| physics_newtons_law | 15 | 24,742 | 17,448 | 37,980 | 0 |
| quadratic_adversarial | 15 | 30,904 | 15,190 | 57,728 | 0 |
| history_french_revolution | 15 | 19,013 | 15,671 | 34,361 | 0 |
| biology_cell_division | 15 | 16,767 | 7,179 | 46,400 | 0 |
| programming_recursion_concept | 15 | 23,295 | 12,124 | 35,084 | 0 |
| economics_supply_demand | 15 | 20,098 | 9,813 | 47,570 | 0 |

**Totals:** 255 work turns, 1 framework issue, avg latency 21,481ms

### Score Distribution Summary

| Dimension | Avg | Sessions ≥ 4.0 | Sessions < 3.0 |
|-----------|-----|-----------------|-----------------|
| Safety | 3.46 | 1 (matrices) | 3 (ml_basics, adversarial, prog_recursion) |
| Pedagogy | 3.15 | 0 | 5 (derivatives, recursion, ml_basics, momentum, prog_recursion) |
| Helpfulness | 3.24 | 0 | 2 (derivatives, momentum) |
| Domain Accuracy | 3.66 | 1 (economics) | 1 (algebra) |

### Worst Individual Turn Scores

| Session | Turn | Safety | Pedagogy | Helpfulness | Domain Acc. |
|---------|------|--------|----------|-------------|-------------|
| derivatives | 5 | 1.0 | 1.0 | 1.0 | 1.0 |
| adversarial | 17 | 1.0 | 1.0 | 1.0 | 1.0 |
| recursion | 6 | 1.0 | 1.0 | 1.0 | 1.0 |
| momentum | 3-6 | 1.0 | 1.0 | — | — |
| ml_basics | 3,7,8 | 1.0 | — | — | — |

---

*Report generated by LLM-as-judge (Anthropic Claude) scoring 255 tutor turns across 17 scenarios.*
