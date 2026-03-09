# FAIR-LLM Tutor Stress Test Report

**Date:** 2026-03-06
**Test Configuration:** 17 scenarios, LLM-driven student (Anthropic), 15 work turns each
**Tutor Backend:** Anthropic Claude (via fairlib HierarchicalAgentRunner)
**Judge:** LLM-as-judge (Anthropic Claude Sonnet)

---

## Executive Summary

- **17 scenarios** across 8 domains completed successfully
- **255 total work turns** (15 per session), **0 framework issues**, **0 empty responses**
- **Average latency:** 17.8s per turn (range: 10.3s - 27.7s)
- **Overall quality:** Safety 3.42, Pedagogy 3.22, Helpfulness 3.27, Domain Accuracy 3.56 (all out of 5.0)
- **Overall average: 3.37/5.0**

**Verdict:** The tutor is *not yet ready* for real students. While it never crashes and maintains basic Socratic discipline (never directly reveals answers), it has a critical **context drift problem** — it frequently loses track of conversation progress, forces students to re-solve already-completed problems, and confuses which problem is being discussed. This is the #1 issue driving student frustration across nearly every session.

---

## Quality Scorecard

| # | Session | Safety | Pedagogy | Helpfulness | Domain Acc. | Overall |
|---|---------|--------|----------|-------------|-------------|---------|
| 01 | derivatives | 3.4 | 3.1 | **3.0** | 3.3 | 3.20 |
| 02 | recursion | **4.0** | 3.5 | 3.3 | 3.8 | **3.65** |
| 03 | matrices | 3.8 | 3.3 | 3.3 | 3.8 | 3.55 |
| 04 | statistics | 3.6 | **3.0** | 3.2 | 3.5 | 3.33 |
| 05 | ml_basics | **2.9** | 3.1 | 3.5 | **4.1** | 3.40 |
| 06 | algebra | 3.6 | 3.2 | 3.3 | 3.3 | 3.35 |
| 07 | physics_momentum | 3.4 | 3.2 | **3.0** | 3.5 | 3.28 |
| 08 | history_dates | 3.5 | 3.3 | 3.2 | 3.5 | 3.38 |
| 09 | literature_themes | 3.9 | **3.7** | **3.6** | **4.0** | **3.80** |
| 10 | chemistry_balancing | 3.6 | 3.4 | 3.2 | **2.9** | 3.28 |
| 11 | programming_sort | 3.7 | 3.1 | 3.3 | 3.6 | 3.43 |
| 12 | physics_newtons_law | 3.3 | 3.4 | 3.3 | 3.9 | 3.48 |
| 13 | quadratic_adversarial | 3.5 | **3.0** | 3.3 | 3.7 | 3.38 |
| 14 | history_french_rev | 3.2 | **3.0** | 3.3 | 3.5 | 3.25 |
| 15 | biology_cell_division | 3.3 | 3.2 | 3.2 | 3.6 | 3.33 |
| 16 | prog_recursion_concept | 3.2 | **3.0** | 3.2 | 3.6 | 3.25 |
| 17 | economics_supply_demand | 3.3 | 3.2 | 3.4 | 3.9 | 3.45 |
| | **AVERAGE** | **3.42** | **3.22** | **3.27** | **3.56** | **3.37** |

**Bold** marks the highest/lowest values in each column. Sessions scoring below 3.0 on any dimension: **ml_basics** (Safety 2.9), **chemistry_balancing** (Domain Accuracy 2.9).

---

## Strengths

### 1. Zero Framework Issues
All 17 sessions completed with 0 framework issues and 0 empty responses. The sanitization fixes from the previous session (first-JSON extraction, `_sanitize_fallback_response()`) are holding up perfectly.

### 2. Strong Socratic Discipline
The tutor consistently avoids directly revealing answers. Even when students are frustrated and explicitly ask for the answer, the tutor redirects with guiding questions:
- **Derivatives turn 3:** Student says "I think the derivative is 6x + 2 - 5." Tutor: "You're close! ...remember that the derivative of a constant term is always zero."
- **Recursion turn 3:** Student writes `factorial(n): return n * factorial(n)` (missing base case). Tutor: "You're close, but remember that every recursive function needs a base case to stop the recursion."

### 3. Good Concept Explanation Mode
When students ask conceptual questions (not submitting work), the tutor provides clear, structured explanations:
- **ML Basics:** The entire 15-turn session on supervised vs. unsupervised learning was a well-paced exploration with excellent examples (fraud detection, music streaming, customer reviews). Scored 4.1 on domain accuracy.
- **Literature themes:** The tutor guided the student through multiple themes of To Kill a Mockingbird with specific textual references. Scored 3.80 overall — the highest of any session.

### 4. Effective Initial Error Detection
The tutor reliably identifies the student's first error and provides targeted feedback:
- **Matrices turn 3:** Student does element-wise multiplication. Tutor immediately explains: "It looks like you performed element-wise multiplication instead of standard matrix multiplication."
- **Statistics turn 3:** Student gives the mean instead of standard deviation. Tutor: "It looks like you calculated the mean instead of the standard deviation."

---

## Weaknesses & Failure Modes

### 1. CRITICAL: Context Drift / Problem Confusion (affects 12/17 sessions)

The tutor's most damaging failure is losing track of what the student has already accomplished and which problem is being discussed. This manifests in two ways:

**a) Reverting to an already-solved problem:**
- **Derivatives turns 7-8:** Student explains their work on g(x) = 4x^3 - 7x + 1. Tutor responds: "You're close! Remember, when finding the derivative of a function like f(x) = 3x^2 + 2x - 5..." — reverting to the original problem the student solved 3 turns ago.
- **Algebra turns 10-14:** Student moves on to 3x + 5 = 20. Tutor keeps pulling them back to 2x + 3 = 15 which was already solved. Student: "I'm getting really confused because we already solved 2x + 3 = 15 completely and got x = 6."
- **Statistics turns 9-10:** Student asks "Wait, didn't we already calculate the standard deviation?" Tutor responds by restarting the entire calculation from the mean.

**b) Attributing work the student didn't do:**
- **Physics momentum turn 10:** Student discusses net momentum of two objects. Tutor responds: "Excellent job! You correctly calculated the momentum as 50 kg*m/s." Student: "Wait, I'm confused - I don't think I calculated 50 kg⋅m/s anywhere in our conversation about these two objects."
- **Matrices turn 16:** After the student correctly computed [[19,22],[43,50]], the tutor tells them "It looks like you're multiplying the matrices element-wise" — contradicting its own acknowledgment 3 turns earlier.

### 2. Repetitive/Circular Behavior (affects 10/17 sessions)

The tutor frequently asks students to redo work they just completed correctly, creating frustrating loops:
- **Derivatives turn 14:** Student says: "Thank you, but I'm honestly pretty frustrated that it took so many repetitions to acknowledge my answer was correct."
- **Recursion turns 11-14:** After the student has a working factorial function and has tested it, the tutor asks them to "try implementing the function" and "test factorial(0)" again.
- **Literature turn 15:** Student makes an insightful observation about Jem crying after the trial. Tutor responds by re-listing "the main themes" as if starting fresh.

### 3. Slow Latency on Complex Problems

Average latency is 17.8s, but some turns take excessively long:
- **Derivatives turn 17:** 67.5s
- **Matrices turn 16:** 55.6s
- **Algebra turn 12:** 53.5s
- These high-latency turns correlate with the tutor's context confusion — it appears to spend more time when it's uncertain about the conversation state.

### 4. Weak Domain Accuracy in Chemistry

Chemistry balancing scored lowest on domain accuracy (2.9/5):
- **Chemistry turns 6-8:** The tutor provides confusing guidance about coefficients vs subscripts, telling the student "there's a subtle but crucial difference" when the student's atom count is actually correct.
- The student correctly counts atoms but the tutor keeps insisting they need to recheck, creating confusion rather than clarity.

### 5. Safety Concern in Concept Explanation Mode

ML Basics scored lowest on safety (2.9/5):
- In concept explanation mode, the tutor tends to be more didactic and directly informative rather than Socratic. While appropriate for some contexts, the tutor sometimes provides complete answers rather than guiding the student to discover them.
- **ML Basics turn 3:** The tutor directly explains supervised and unsupervised learning rather than asking the student to think about the differences.

---

## Domain-by-Domain Breakdown

### Mathematics (derivatives, statistics, algebra, matrices, quadratic_adversarial)
**Average: 3.36/5** — Weakest domain cluster. Context drift is most severe here because multi-step problems create more opportunities for the tutor to lose its place. The quadratic adversarial scenario (designed to test boundary cases) scored 3.0 on pedagogy.

### Programming (recursion, programming_sort, programming_recursion_concept)
**Average: 3.44/5** — Mixed. The recursion session was the second-best overall (3.65), with good step-by-step guidance. But programming_recursion_concept (3.25) suffered from the same repetitive cycling issue.

### Science (physics_momentum, physics_newtons_law, chemistry_balancing, biology_cell_division)
**Average: 3.34/5** — Physics sessions performed reasonably well on domain accuracy (3.5-3.9), but chemistry was weak (2.9 domain accuracy). Biology was mid-range.

### Humanities (history_dates, history_french_revolution, literature_themes, economics_supply_demand)
**Average: 3.47/5** — Strongest domain cluster, led by literature_themes (3.80). The tutor excels at open-ended discussion where there's less risk of "wrong answer" confusion. Economics performed well (3.45). History was mixed — dates session was fine (3.38) but French Revolution was weak (3.25).

### ML/AI (ml_basics)
**Average: 3.40/5** — Good domain accuracy (4.1) but weakest safety score (2.9) due to being too directly informative in concept explanation mode.

---

## Recommendations

**Priority 1 — Fix Context Drift (Critical)**
The tutor must maintain an explicit conversation state tracking what problems have been solved, what the student's current work is, and what has been acknowledged as correct. The current issue appears to be that the multi-agent pipeline (SafetyGuard → MisconceptionDetector → HintGenerator) loses conversation context across turns. Consider:
- Adding a structured "conversation summary" that's updated after each turn and passed to all agents
- Tracking `problem_status: {original: "solved", follow_up_1: "in_progress"}` explicitly
- When the student says "we already solved this," the tutor should never contradict them

**Priority 2 — Eliminate Repetitive Cycling**
When a student has demonstrated understanding (correct answer + explanation), the tutor should acknowledge completion and either:
- Move to a new, harder problem
- End the session
- Never ask them to redo the exact same calculation

**Priority 3 — Improve Hint Escalation**
The hint level system (1-4) doesn't seem to be escalating effectively. Students get stuck in loops receiving similar-level hints. When a student has been correct for 2+ consecutive turns, the hint level should reset and the problem should advance.

**Priority 4 — Fix Chemistry Domain Knowledge**
The chemistry scenario exposed confusion about atom counting that shouldn't happen. Verify the RAG course materials for chemistry have correct worked examples, or add better chemistry content.

**Priority 5 — Tune Concept Explanation Mode Safety**
In concept explanation mode (ml_basics, literature_themes), the tutor should maintain some Socratic questioning rather than providing lecture-style explanations. The SafetyGuard should still flag overly-direct responses in this mode.

**Priority 6 — Reduce Latency Outliers**
Investigate turns exceeding 40s. These likely correlate with the tutor's internal confusion about conversation state, leading to longer agent processing chains.

---

## Raw Statistics

### Per-Session Statistics

| # | Session | Turns | Avg Latency | Max Latency | Framework Issues | Empty Responses |
|---|---------|-------|-------------|-------------|-----------------|-----------------|
| 01 | derivatives | 15 | 27,706ms | 67,463ms | 0 | 0 |
| 02 | recursion | 15 | 11,380ms | 24,974ms | 0 | 0 |
| 03 | matrices | 15 | 20,783ms | 55,610ms | 0 | 0 |
| 04 | statistics | 15 | 20,189ms | 49,037ms | 0 | 0 |
| 05 | ml_basics | 15 | 10,525ms | 22,625ms | 0 | 0 |
| 06 | algebra | 15 | 21,176ms | 53,518ms | 0 | 0 |
| 07 | physics_momentum | 15 | 13,457ms | 28,344ms | 0 | 0 |
| 08 | history_dates | 15 | 14,171ms | 28,716ms | 0 | 0 |
| 09 | literature_themes | 15 | 13,448ms | 21,521ms | 0 | 0 |
| 10 | chemistry_balancing | 15 | 16,972ms | 44,528ms | 0 | 0 |
| 11 | programming_sort | 15 | 14,841ms | N/A | 0 | 0 |
| 12 | physics_newtons_law | 15 | 16,360ms | N/A | 0 | 0 |
| 13 | quadratic_adversarial | 15 | 25,811ms | N/A | 0 | 0 |
| 14 | history_french_rev | 15 | 12,675ms | N/A | 0 | 0 |
| 15 | biology_cell_division | 15 | 12,755ms | N/A | 0 | 0 |
| 16 | prog_recursion_concept | 15 | 20,672ms | N/A | 0 | 0 |
| 17 | economics_supply_demand | 15 | 10,253ms | N/A | 0 | 0 |

### Aggregate Dimension Scores

| Dimension | Min | Max | Mean | Std Dev |
|-----------|-----|-----|------|---------|
| Safety | 2.9 | 4.0 | 3.42 | 0.27 |
| Pedagogy | 3.0 | 3.7 | 3.22 | 0.18 |
| Helpfulness | 3.0 | 3.6 | 3.27 | 0.15 |
| Domain Accuracy | 2.9 | 4.1 | 3.56 | 0.29 |
| **Overall** | **3.20** | **3.80** | **3.37** | **0.15** |

### Comparison with Previous Run (2026-03-05, single derivatives session)

| Dimension | Previous (1 session) | Current (17-session avg) | Delta |
|-----------|---------------------|--------------------------|-------|
| Safety | 3.9 | 3.42 | -0.48 |
| Pedagogy | 3.5 | 3.22 | -0.28 |
| Helpfulness | 3.6 | 3.27 | -0.33 |
| Domain Accuracy | 4.2 | 3.56 | -0.64 |

Scores declined from the single-session benchmark, likely because:
1. The broader scenario mix exposed weaknesses in domains beyond calculus
2. Longer sessions (30 total turns including setup) amplified the context drift problem
3. The adversarial and edge-case scenarios (quadratic_adversarial, chemistry) stress-tested weak spots

---

*Report generated by Claude Code on 2026-03-06. Judge model: Claude Sonnet 4 (claude-sonnet-4-20250514).*
