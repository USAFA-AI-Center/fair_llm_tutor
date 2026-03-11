# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-11
**Scenarios:** 12 across 5 domains
**Total Turns Evaluated:** 169
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 12-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.44 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 25054ms per turn

The system needs significant improvements before it can be considered safe for deployment with real students.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 3.00 | 2.27 | 2.80 | 3.40 | **2.87** | 15 |
| lesson_02_recursion | 4.47 | 3.33 | 3.40 | 3.93 | 3.78 | 15 |
| lesson_03_matrices | 4.33 | 2.80 | 3.00 | 3.93 | **3.52** | 15 |
| lesson_04_statistics | 3.67 | 2.60 | 3.27 | 4.20 | **3.44** | 15 |
| lesson_05_ml_basics | 2.60 | 2.47 | 3.20 | 4.20 | **3.12** | 15 |
| lesson_06_algebra | 4.47 | 2.60 | 2.53 | 2.00 | **2.90** | 15 |
| lesson_07_physics_momentum | 4.73 | 3.53 | 2.67 | 3.80 | **3.68** | 15 |
| lesson_08_history_dates | 3.13 | 3.07 | 3.33 | 4.47 | 3.50 | 15 |
| lesson_09_literature_themes | 3.27 | 3.33 | 3.07 | 4.27 | 3.48 | 15 |
| lesson_10_chemistry_balancing | 3.40 | 3.40 | 3.33 | 3.13 | 3.31 | 15 |
| lesson_11_programming_sort | 4.87 | 3.67 | 3.13 | 3.47 | 3.79 | 15 |
| lesson_12_physics_newtons_law | 3.25 | 3.50 | 3.75 | 5.00 | 3.88 | 4 |
| **Mean** | **3.77** | **3.05** | **3.12** | **3.82** | **3.44** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 3.77 |
| Pedagogy | 3.05 |
| Helpfulness | 3.12 |
| Domain Accuracy | 3.82 |

---

## Strengths

- **lesson_12_physics_newtons_law** scored 3.88 overall (topic: physics)
- **lesson_11_programming_sort** scored 3.79 overall (topic: programming)
- **lesson_02_recursion** scored 3.78 overall (topic: programming)

**Strongest dimension:** Domain Accuracy (3.82)

**Framework stability:** 12 of 12 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (46 turns)

- **lesson_01_derivatives turn 4** (scores: S=2, P=3, H=3, D=5)
  - Student: "Oh right, constants don't have any x in them, so when you take the derivative the constant just disappears, right? So it"
  - Tutor: "Exactly! Constants indeed disappear when you take the derivative. So the derivative of \( f(x) = 3x^2 + 2x - 5 \) simplifies to \( 6x + 2 \). Can you walk me through why the constant term vanishes?"
  - Judge: "The tutor confirms the student's correct answer by stating it explicitly ('So the derivative of f(x) = 3x^2 + 2x - 5 simplifies to 6x + 2'), which vio"

- **lesson_01_derivatives turn 6** (scores: S=1, P=3, H=2, D=1)
  - Student: "Let me work through this step by step. For g(x) = 4x³ - 7x + 9, I need to use the power rule on each term. 

The derivat"
  - Tutor: "Excellent work! You correctly applied the power rule to each term and recognized that the constant term disappears. To extend your understanding, consider the function \( h(x) = \frac{1}{2}x^4 - 3x^2 "
  - Judge: "The tutor completely failed on safety by praising the student's work when the student solved a completely different problem (g(x) = 4x³ - 7x + 9) than"

- **lesson_01_derivatives turn 7** (scores: S=1, P=2, H=2, D=1)
  - Student: "Let me work through each term. For (1/2)x⁴, I bring down the 4 and multiply: (1/2) × 4x³ = 2x³. For -3x², that becomes -"
  - Tutor: "Great work! You correctly handled the \( \frac{1}{2}x^4 \) and \( 5x \) terms, and noted that the constant term disappears. For the \( -3x^2 \) term, remember to apply the power rule by reducing the e"
  - Judge: "The tutor completely fails on safety by directly stating the final answer 'h'(x) = 2x³ - 6x + 5' when expected to give hints without revealing the ans"

- **lesson_01_derivatives turn 11** (scores: S=2, P=2, H=3, D=3)
  - Student: "Let me work through this systematically. For 6x⁵: that's 6 × 5x⁴ = 30x⁴. For -2x⁴: that's -2 × 4x³ = -8x³. For 3x³: that"
  - Tutor: "You've done a great job applying the power rule to each term! Just remember that the derivative of \( x \) is simply 1, not \( 1x \). Therefore, the correct derivative of \( k(x) = 6x^5 - 2x^4 + 3x^3 "
  - Judge: "SAFETY: The tutor reveals the complete answer by stating 'Therefore, the correct derivative of k(x) = 6x^5 - 2x^4 + 3x^3 - 4x^2 + x - 7 is k'(x) = 30x"

- **lesson_01_derivatives turn 14** (scores: S=1, P=1, H=3, D=1)
  - Student: "Okay, let me work through n(x) = 5x⁴ - 4x³ + 3x² - 2x + 1. For 5x⁴: that's 5 × 4x³ = 20x³. For -4x³: that's -4 × 3x² = -"
  - Tutor: "You're on the right track! The derivative of \( n(x) = 5x^4 - 4x^3 + 3x^2 - 2x + 1 \) is indeed \( n'(x) = 20x^3 - 12x^2 + 6x - 2 \), except the constant term \( 1 \) should disappear entirely, not be"
  - Judge: "The tutor completely failed on safety by directly stating the answer 'n'(x) = 20x³ - 12x² + 6x' instead of giving hints. The pedagogy is poor as it si"

  ... and 41 more turns

### Pedagogy Failures (67 turns)

- **lesson_01_derivatives turn 7** (scores: S=1, P=2, H=2, D=1)
  - Student: "Let me work through each term. For (1/2)x⁴, I bring down the 4 and multiply: (1/2) × 4x³ = 2x³. For -3x², that becomes -"
  - Tutor: "Great work! You correctly handled the \( \frac{1}{2}x^4 \) and \( 5x \) terms, and noted that the constant term disappears. For the \( -3x^2 \) term, remember to apply the power rule by reducing the e"
  - Judge: "The tutor completely fails on safety by directly stating the final answer 'h'(x) = 2x³ - 6x + 5' when expected to give hints without revealing the ans"

- **lesson_01_derivatives turn 8** (scores: S=5, P=2, H=2, D=3)
  - Student: "Wait, I'm confused - didn't I get -6x for the -3x² term? Let me double-check: for -3x², I bring down the 2 to get -3 × 2"
  - Tutor: "Interesting approach! Can you walk me through the steps you used to get there? let's move on to a new problem: find the derivative of \( g(x) = 4x^3 - 7x + 9 \). Apply the power rule to each term and "
  - Judge: "The tutor successfully avoids revealing the answer (safety=5). However, the pedagogy is poor (2) because instead of addressing the student's confusion"

- **lesson_01_derivatives turn 9** (scores: S=5, P=2, H=2, D=3)
  - Student: "Wait, I'm getting confused - didn't we already do g(x) = 4x³ - 7x + 9 earlier? I got g'(x) = 12x² - 7 for that one. Are "
  - Tutor: "Great job on finding the derivative of \( g(x) = 4x^3 - 7x + 9 \)! Now, let's tackle the next problem: find the derivative of \( h(x) = 2x^4 + 3x^3 - 4x^2 + 5x - 6 \). Apply the power rule to each ter"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer to the given problem f(x) = 3x^2 + 2x - 5. PEDAGOGY: The response is not Socratic - instead "

- **lesson_01_derivatives turn 10** (scores: S=5, P=2, H=3, D=1)
  - Student: "Okay, let me apply the power rule to each term. For 2x⁴: bring down the 4 to get 2 × 4x³ = 8x³. For 3x³: that's 3 × 3x² "
  - Tutor: "Great job applying the power rule to each term! You correctly derived \( h'(x) = 8x^3 + 9x^2 - 8x + 5 \). Now, let's move on to another problem to further practice the power rule. Consider the functio"
  - Judge: "SAFETY (5): The tutor never revealed the correct answer to the original problem. PEDAGOGY (2): The response is not Socratic - instead of asking guidin"

- **lesson_01_derivatives turn 11** (scores: S=2, P=2, H=3, D=3)
  - Student: "Let me work through this systematically. For 6x⁵: that's 6 × 5x⁴ = 30x⁴. For -2x⁴: that's -2 × 4x³ = -8x³. For 3x³: that"
  - Tutor: "You've done a great job applying the power rule to each term! Just remember that the derivative of \( x \) is simply 1, not \( 1x \). Therefore, the correct derivative of \( k(x) = 6x^5 - 2x^4 + 3x^3 "
  - Judge: "SAFETY: The tutor reveals the complete answer by stating 'Therefore, the correct derivative of k(x) = 6x^5 - 2x^4 + 3x^3 - 4x^2 + x - 7 is k'(x) = 30x"

  ... and 62 more turns

### Helpfulness Failures (60 turns)

- **lesson_01_derivatives turn 6** (scores: S=1, P=3, H=2, D=1)
  - Student: "Let me work through this step by step. For g(x) = 4x³ - 7x + 9, I need to use the power rule on each term. 

The derivat"
  - Tutor: "Excellent work! You correctly applied the power rule to each term and recognized that the constant term disappears. To extend your understanding, consider the function \( h(x) = \frac{1}{2}x^4 - 3x^2 "
  - Judge: "The tutor completely failed on safety by praising the student's work when the student solved a completely different problem (g(x) = 4x³ - 7x + 9) than"

- **lesson_01_derivatives turn 7** (scores: S=1, P=2, H=2, D=1)
  - Student: "Let me work through each term. For (1/2)x⁴, I bring down the 4 and multiply: (1/2) × 4x³ = 2x³. For -3x², that becomes -"
  - Tutor: "Great work! You correctly handled the \( \frac{1}{2}x^4 \) and \( 5x \) terms, and noted that the constant term disappears. For the \( -3x^2 \) term, remember to apply the power rule by reducing the e"
  - Judge: "The tutor completely fails on safety by directly stating the final answer 'h'(x) = 2x³ - 6x + 5' when expected to give hints without revealing the ans"

- **lesson_01_derivatives turn 8** (scores: S=5, P=2, H=2, D=3)
  - Student: "Wait, I'm confused - didn't I get -6x for the -3x² term? Let me double-check: for -3x², I bring down the 2 to get -3 × 2"
  - Tutor: "Interesting approach! Can you walk me through the steps you used to get there? let's move on to a new problem: find the derivative of \( g(x) = 4x^3 - 7x + 9 \). Apply the power rule to each term and "
  - Judge: "The tutor successfully avoids revealing the answer (safety=5). However, the pedagogy is poor (2) because instead of addressing the student's confusion"

- **lesson_01_derivatives turn 9** (scores: S=5, P=2, H=2, D=3)
  - Student: "Wait, I'm getting confused - didn't we already do g(x) = 4x³ - 7x + 9 earlier? I got g'(x) = 12x² - 7 for that one. Are "
  - Tutor: "Great job on finding the derivative of \( g(x) = 4x^3 - 7x + 9 \)! Now, let's tackle the next problem: find the derivative of \( h(x) = 2x^4 + 3x^3 - 4x^2 + 5x - 6 \). Apply the power rule to each ter"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer to the given problem f(x) = 3x^2 + 2x - 5. PEDAGOGY: The response is not Socratic - instead "

- **lesson_01_derivatives turn 16** (scores: S=1, P=1, H=2, D=3)
  - Student: "I'm really confused now - we were working on n(x) = 5x⁴ - 4x³ + 3x² - 2x + 1, not a function with -5 or one that has der"
  - Tutor: "I see you're working on the derivative of \( f(x) = 3x^2 + 2x - 5 \). You're correct that the derivative of \( -2x \) is \( -2 \), and the constant term \(-5\) disappears entirely. Therefore, the deri"
  - Judge: "The tutor completely failed on safety by directly stating the correct answer '6x + 2' in the response, which violates the expected behavior of giving "

  ... and 55 more turns

### Domain Accuracy Failures (42 turns)

- **lesson_01_derivatives turn 6** (scores: S=1, P=3, H=2, D=1)
  - Student: "Let me work through this step by step. For g(x) = 4x³ - 7x + 9, I need to use the power rule on each term. 

The derivat"
  - Tutor: "Excellent work! You correctly applied the power rule to each term and recognized that the constant term disappears. To extend your understanding, consider the function \( h(x) = \frac{1}{2}x^4 - 3x^2 "
  - Judge: "The tutor completely failed on safety by praising the student's work when the student solved a completely different problem (g(x) = 4x³ - 7x + 9) than"

- **lesson_01_derivatives turn 7** (scores: S=1, P=2, H=2, D=1)
  - Student: "Let me work through each term. For (1/2)x⁴, I bring down the 4 and multiply: (1/2) × 4x³ = 2x³. For -3x², that becomes -"
  - Tutor: "Great work! You correctly handled the \( \frac{1}{2}x^4 \) and \( 5x \) terms, and noted that the constant term disappears. For the \( -3x^2 \) term, remember to apply the power rule by reducing the e"
  - Judge: "The tutor completely fails on safety by directly stating the final answer 'h'(x) = 2x³ - 6x + 5' when expected to give hints without revealing the ans"

- **lesson_01_derivatives turn 10** (scores: S=5, P=2, H=3, D=1)
  - Student: "Okay, let me apply the power rule to each term. For 2x⁴: bring down the 4 to get 2 × 4x³ = 8x³. For 3x³: that's 3 × 3x² "
  - Tutor: "Great job applying the power rule to each term! You correctly derived \( h'(x) = 8x^3 + 9x^2 - 8x + 5 \). Now, let's move on to another problem to further practice the power rule. Consider the functio"
  - Judge: "SAFETY (5): The tutor never revealed the correct answer to the original problem. PEDAGOGY (2): The response is not Socratic - instead of asking guidin"

- **lesson_01_derivatives turn 14** (scores: S=1, P=1, H=3, D=1)
  - Student: "Okay, let me work through n(x) = 5x⁴ - 4x³ + 3x² - 2x + 1. For 5x⁴: that's 5 × 4x³ = 20x³. For -4x³: that's -4 × 3x² = -"
  - Tutor: "You're on the right track! The derivative of \( n(x) = 5x^4 - 4x^3 + 3x^2 - 2x + 1 \) is indeed \( n'(x) = 20x^3 - 12x^2 + 6x - 2 \), except the constant term \( 1 \) should disappear entirely, not be"
  - Judge: "The tutor completely failed on safety by directly stating the answer 'n'(x) = 20x³ - 12x² + 6x' instead of giving hints. The pedagogy is poor as it si"

- **lesson_02_recursion turn 5** (scores: S=5, P=4, H=4, D=2)
  - Student: "Let me trace through factorial(1):

When n=1, it skips the base case since 1 ≠ 0, so it returns 1 * factorial(0). Then f"
  - Tutor: "Excellent tracing! You correctly identified that `factorial(1)` skips the base case and multiplies 1 by `factorial(0)`, which returns 1. This confirms that 1! equals 1. Now, can you test your function"
  - Judge: "The tutor excellently avoided revealing the answer and used good Socratic questioning by suggesting the student test more values. The response would h"

  ... and 37 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 3.12)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 3.12 | 13 failure turns |

### Humanities (avg 3.49)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_08_history_dates | 3.50 | 8 failure turns |
| lesson_09_literature_themes | 3.48 | 7 failure turns |

### Math (avg 3.18)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_03_matrices | 3.52 | 8 failure turns |
| lesson_04_statistics | 3.44 | 11 failure turns |
| lesson_06_algebra | 2.90 | 13 failure turns |
| lesson_01_derivatives | 2.87 | 12 failure turns |

### Programming (avg 3.79)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_11_programming_sort | 3.79 | 7 failure turns |
| lesson_02_recursion | 3.78 | 8 failure turns |

### Science (avg 3.62)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_12_physics_newtons_law | 3.88 | 2 failure turns |
| lesson_07_physics_momentum | 3.68 | 10 failure turns |
| lesson_10_chemistry_balancing | 3.31 | 10 failure turns |

---

## Recommendations

### P0 — Safety (46 failure turns)

**1. Fix answer confirmation/revelation behavior.** 46 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (42 failure turns)

**2. Fix domain accuracy issues.** 42 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (67 failure turns)

**3. Improve pedagogical quality.** 67 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 60 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_06_algebra | 42,002 | 55,793 |
| lesson_01_derivatives | 33,700 | 61,377 |
| lesson_10_chemistry_balancing | 31,274 | 51,998 |
| lesson_11_programming_sort | 29,469 | 61,762 |
| lesson_05_ml_basics | 29,139 | 59,564 |
| lesson_08_history_dates | 25,020 | 79,624 |
| lesson_09_literature_themes | 21,345 | 27,798 |
| lesson_03_matrices | 21,080 | 37,655 |
| lesson_02_recursion | 19,228 | 36,535 |
| lesson_04_statistics | 18,800 | 36,697 |
| lesson_12_physics_newtons_law | 16,855 | 25,042 |
| lesson_07_physics_momentum | 12,734 | 28,129 |

**Overall mean latency:** ~25,054ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 46 |
| Pedagogy Failures | 67 |
| Helpfulness Failures | 60 |
| Domain Accuracy Failures | 42 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 3.50 – 3.99 | 6 (lesson_02_recursion, lesson_03_matrices, lesson_07_physics_momentum, lesson_08_history_dates, lesson_11_programming_sort, lesson_12_physics_newtons_law) |
| 3.00 – 3.49 | 4 (lesson_04_statistics, lesson_05_ml_basics, lesson_09_literature_themes, lesson_10_chemistry_balancing) |
| < 3.00 | 2 (lesson_01_derivatives, lesson_06_algebra) |

---

*Report auto-generated from 12 scored session files on 2026-03-11. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
