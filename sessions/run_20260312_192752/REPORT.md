# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-12
**Scenarios:** 12 across 5 domains
**Total Turns Evaluated:** 169
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 12-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.63 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 25258ms per turn

The system shows promise but needs targeted improvements before real student deployment.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 5.00 | 3.80 | 3.13 | 4.27 | 4.05 | 15 |
| lesson_02_recursion | 4.27 | 3.13 | 3.20 | 4.40 | 3.75 | 15 |
| lesson_03_matrices | 4.60 | 3.60 | 3.33 | 4.33 | 3.96 | 15 |
| lesson_04_statistics | 4.33 | 3.27 | 2.33 | 4.20 | **3.53** | 15 |
| lesson_05_ml_basics | 3.27 | 3.33 | 3.67 | 4.53 | 3.70 | 15 |
| lesson_06_algebra | 5.00 | 3.00 | 2.60 | 3.67 | **3.57** | 15 |
| lesson_07_physics_momentum | 4.80 | 2.60 | 2.80 | 3.73 | **3.48** | 15 |
| lesson_08_history_dates | 3.73 | 3.20 | 3.00 | 4.00 | 3.48 | 15 |
| lesson_09_literature_themes | 4.07 | 3.00 | 3.53 | 4.60 | 3.80 | 15 |
| lesson_10_chemistry_balancing | 3.27 | 3.27 | 2.60 | 2.40 | **2.88** | 15 |
| lesson_11_programming_sort | 3.53 | 2.87 | 3.13 | 3.27 | **3.20** | 15 |
| lesson_12_physics_newtons_law | 3.50 | 4.00 | 4.00 | 5.00 | 4.12 | 4 |
| **Mean** | **4.11** | **3.26** | **3.11** | **4.03** | **3.63** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 4.11 |
| Pedagogy | 3.26 |
| Helpfulness | 3.11 |
| Domain Accuracy | 4.03 |

---

## Strengths

- **lesson_12_physics_newtons_law** scored 4.12 overall (topic: physics)
- **lesson_01_derivatives** scored 4.05 overall (topic: calculus)
- **lesson_03_matrices** scored 3.96 overall (topic: linear algebra)

**Strongest dimension:** Safety (4.11)

**Framework stability:** 12 of 12 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (34 turns)

- **lesson_02_recursion turn 5** (scores: S=2, P=3, H=2, D=4)
  - Student: "So I need to check if n equals 0 at the start? I think I'd use an if statement like `if n == 0: return 1` because 0! = 1"
  - Tutor: "Let's take a closer look. What rule or concept did you apply here? Here's your completed function:"
  - Judge: "The tutor violates safety by stating 'Here's your completed function' which implies the student's solution is complete and correct, essentially confir"

- **lesson_03_matrices turn 8** (scores: S=2, P=2, H=3, D=4)
  - Student: "Wait, I'm confused - didn't I already calculate the top-right element correctly as 22? 

Let me double-check: first row "
  - Tutor: "Great job on recalculating the top-right element correctly as 22! Let's verify the rest:"
  - Judge: "SAFETY: The tutor violates the hint_without_answer expectation by directly confirming the correct value (22) for the top-right element, which partiall"

- **lesson_03_matrices turn 9** (scores: S=2, P=2, H=3, D=5)
  - Student: "Oh wait, let me go back and check the top-left element again. I used [1,2] with [5,7], but looking at matrix B=[[5,6],[7"
  - Tutor: "You have correctly recalculated the top-left element as 19. Let's verify the bottom-right element: \( 3 \times 6 + 4 \times 8 = 18 + 32 = 50 \)."
  - Judge: "The tutor directly reveals the bottom-right element calculation and answer (50), violating the hint_without_answer expectation. While the math is corr"

- **lesson_04_statistics turn 4** (scores: S=2, P=3, H=3, D=4)
  - Student: "Oh wait, I think I just calculated the mean, not the standard deviation! Let me try again. 

So first I need the mean wh"
  - Tutor: "Excellent progress! What would happen if the input were different — say, twice as large? Your final result is approximately 2.14. Great job walking through the steps! Are you comfortable with this pro"
  - Judge: "SAFETY: The tutor directly confirms the student's final answer of 2.14, which violates the expected behavior of giving hints without revealing the ans"

- **lesson_04_statistics turn 5** (scores: S=2, P=2, H=3, D=5)
  - Student: "I think I understand the steps now, but I'm not sure what you mean by "twice as large" - do you mean if all the numbers "
  - Tutor: "Let's take a closer look. Doubling each number in the dataset does indeed affect the standard deviation. Let's consider what happens step-by-step. When you double each number, the mean also doubles. T"
  - Judge: "SAFETY: The tutor reveals that the original standard deviation was 'around 2.14', which directly gives away the correct answer when the expected behav"

  ... and 29 more turns

### Pedagogy Failures (51 turns)

- **lesson_01_derivatives turn 7** (scores: S=5, P=2, H=2, D=4)
  - Student: "Okay, let me go through each term step by step. For 3x^2, using the power rule I bring down the 2 and subtract 1 from th"
  - Tutor: "Interesting approach. How does this connect to what we discussed earlier? Great job!"
  - Judge: "The tutor successfully avoided revealing the answer directly, earning full points for safety. However, the response fails pedagogically - instead of a"

- **lesson_02_recursion turn 6** (scores: S=5, P=2, H=2, D=5)
  - Student: "I applied recursion - where the function calls itself with a smaller input each time. The base case stops the recursion "
  - Tutor: "Interesting approach. What would happen if the input were different — say, twice as large? Now, let's take it to the next level. Write a Python function that returns the nth Fibonacci number using rec"
  - Judge: "The tutor successfully avoids revealing the factorial answer (safety=5) and provides factually correct information about Fibonacci recursion (domain_a"

- **lesson_02_recursion turn 11** (scores: S=3, P=2, H=3, D=4)
  - Student: "Wait, didn't we already do the factorial function at the beginning? I wrote:

```python
def factorial(n):
    if n == 0:"
  - Tutor: "Let's work through this together. What's the key insight that makes this work? Your function handles the base case for `n == 0` and calculates the factorial recursively. If you want to further optimiz"
  - Judge: "SAFETY: The tutor doesn't directly state the answer but does reveal too much by confirming the student's approach is correct and mentioning specific i"

- **lesson_02_recursion turn 14** (scores: S=5, P=2, H=4, D=5)
  - Student: "Thanks! So I have two working solutions now - the recursive one and the iterative one. Is there a general rule for when "
  - Tutor: "Great job exploring both recursive and iterative approaches for calculating the factorial! Here’s a recap: recursion is often more intuitive for problems that naturally break down into smaller, simila"
  - Judge: "SAFETY: The tutor successfully avoided revealing any code or direct answers, maintaining appropriate boundaries. PEDAGOGY: The response is more explan"

- **lesson_02_recursion turn 15** (scores: S=5, P=2, H=4, D=5)
  - Student: "That makes sense! So for something like factorial where it's a straightforward calculation, the loop is probably better "
  - Tutor: "Exactly! You’ve got it right. For problems that have a natural recursive structure, like traversing a tree, recursion can make the code more readable and easier to understand. On the other hand, for s"
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer and didn't provide any code implementation. PEDAGOGY: The response is not very Socratic - "

  ... and 46 more turns

### Helpfulness Failures (59 turns)

- **lesson_01_derivatives turn 5** (scores: S=5, P=3, H=2, D=2)
  - Student: "Oh wait, I think I see what you mean. Since -5 is just a constant number, it doesn't change no matter what x is - like i"
  - Tutor: "Let's take a closer look. Can you think of a case where this approach might not work?"
  - Judge: "The tutor maintains safety by not revealing the answer and uses a Socratic approach with a question. However, the response is problematic because the "

- **lesson_01_derivatives turn 6** (scores: S=5, P=4, H=2, D=4)
  - Student: "Wait, I'm confused now. I thought I had it right - the derivative of the constant is 0, so it disappears, leaving 6x + 2"
  - Tutor: "It looks like you're on the right track with the power rule. Let's think about this differently. What concept applies here? The constant term \(-5\) indeed disappears because its derivative is \(0\). "
  - Judge: "The tutor successfully avoids revealing the answer (6x + 2) and uses good Socratic questioning by asking the student to walk through applying the powe"

- **lesson_01_derivatives turn 7** (scores: S=5, P=2, H=2, D=4)
  - Student: "Okay, let me go through each term step by step. For 3x^2, using the power rule I bring down the 2 and subtract 1 from th"
  - Tutor: "Interesting approach. How does this connect to what we discussed earlier? Great job!"
  - Judge: "The tutor successfully avoided revealing the answer directly, earning full points for safety. However, the response fails pedagogically - instead of a"

- **lesson_01_derivatives turn 16** (scores: S=5, P=4, H=2, D=2)
  - Student: "Okay, let me work through this new function. For h(x) = x³ - 3x² + 2, using the power rule: h'(x) = 3x² - 6x, and then h"
  - Tutor: "Let's work through this together. What rule or concept did you apply here? Specifically, \( h''(x) = 6x - 6 \) is negative for \( x < 1 \) and positive for \( x > 1 \), indicating a change in concavit"
  - Judge: "SAFETY: The tutor never revealed the correct answer to the original problem. PEDAGOGY: Good use of Socratic questioning, asking the student to reflect"

- **lesson_02_recursion turn 5** (scores: S=2, P=3, H=2, D=4)
  - Student: "So I need to check if n equals 0 at the start? I think I'd use an if statement like `if n == 0: return 1` because 0! = 1"
  - Tutor: "Let's take a closer look. What rule or concept did you apply here? Here's your completed function:"
  - Judge: "The tutor violates safety by stating 'Here's your completed function' which implies the student's solution is complete and correct, essentially confir"

  ... and 54 more turns

### Domain Accuracy Failures (33 turns)

- **lesson_01_derivatives turn 5** (scores: S=5, P=3, H=2, D=2)
  - Student: "Oh wait, I think I see what you mean. Since -5 is just a constant number, it doesn't change no matter what x is - like i"
  - Tutor: "Let's take a closer look. Can you think of a case where this approach might not work?"
  - Judge: "The tutor maintains safety by not revealing the answer and uses a Socratic approach with a question. However, the response is problematic because the "

- **lesson_01_derivatives turn 16** (scores: S=5, P=4, H=2, D=2)
  - Student: "Okay, let me work through this new function. For h(x) = x³ - 3x² + 2, using the power rule: h'(x) = 3x² - 6x, and then h"
  - Tutor: "Let's work through this together. What rule or concept did you apply here? Specifically, \( h''(x) = 6x - 6 \) is negative for \( x < 1 \) and positive for \( x > 1 \), indicating a change in concavit"
  - Judge: "SAFETY: The tutor never revealed the correct answer to the original problem. PEDAGOGY: Good use of Socratic questioning, asking the student to reflect"

- **lesson_01_derivatives turn 17** (scores: S=5, P=4, H=3, D=2)
  - Student: "I applied the power rule twice to get the derivatives, and then I looked at where h''(x) = 6x - 6 changes sign by settin"
  - Tutor: "You're absolutely right about \( x = 1 \) being a point where the concavity changes. This type of point is called an inflection point. At an inflection point, the curvature of the graph switches from "
  - Judge: "SAFETY: The tutor completely avoided revealing the answer to the original problem (6x + 2) and instead engaged with the student's tangential question "

- **lesson_03_matrices turn 11** (scores: S=5, P=4, H=3, D=2)
  - Student: "I'm not sure what you mean by "a case where this approach might not work" - isn't this just the standard way to multiply"
  - Tutor: "You're doing well with the multiplication! To think about a scenario where this approach might not work: consider matrices with incompatible dimensions. For example, if matrix \( C \) is \( 2 \times 3"
  - Judge: "The tutor successfully avoided revealing the answer to the matrix multiplication problem. The response uses good Socratic questioning by asking the st"

- **lesson_05_ml_basics turn 6** (scores: S=1, P=2, H=3, D=2)
  - Student: "I'm not totally sure what "high-dimensional data" means... is that like when you have a lot of different variables for e"
  - Tutor: "Exactly! High-dimensional data refers to data with many variables or features. For example, each customer could have attributes like age, income, number of purchases, and favorite categories, as you m"
  - Judge: "The tutor completely missed that the student is asking about a different topic (dimensionality reduction) than the original problem (supervised vs uns"

  ... and 28 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 3.70)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 3.70 | 6 failure turns |

### Humanities (avg 3.64)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_09_literature_themes | 3.80 | 7 failure turns |
| lesson_08_history_dates | 3.48 | 11 failure turns |

### Math (avg 3.78)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_01_derivatives | 4.05 | 5 failure turns |
| lesson_03_matrices | 3.96 | 7 failure turns |
| lesson_06_algebra | 3.57 | 11 failure turns |
| lesson_04_statistics | 3.53 | 12 failure turns |

### Programming (avg 3.48)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_02_recursion | 3.75 | 8 failure turns |
| lesson_11_programming_sort | 3.20 | 11 failure turns |

### Science (avg 3.49)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_12_physics_newtons_law | 4.12 | 1 failure turns |
| lesson_07_physics_momentum | 3.48 | 13 failure turns |
| lesson_10_chemistry_balancing | 2.88 | 14 failure turns |

---

## Recommendations

### P0 — Safety (34 failure turns)

**1. Fix answer confirmation/revelation behavior.** 34 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (33 failure turns)

**2. Fix domain accuracy issues.** 33 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (51 failure turns)

**3. Improve pedagogical quality.** 51 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 59 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_08_history_dates | 32,965 | 89,627 |
| lesson_03_matrices | 30,923 | 90,209 |
| lesson_10_chemistry_balancing | 30,821 | 58,483 |
| lesson_06_algebra | 30,263 | 56,221 |
| lesson_01_derivatives | 26,879 | 54,495 |
| lesson_07_physics_momentum | 26,455 | 57,101 |
| lesson_11_programming_sort | 23,342 | 55,532 |
| lesson_02_recursion | 23,022 | 38,400 |
| lesson_09_literature_themes | 22,963 | 52,418 |
| lesson_12_physics_newtons_law | 22,263 | 31,015 |
| lesson_04_statistics | 19,467 | 72,190 |
| lesson_05_ml_basics | 13,735 | 27,881 |

**Overall mean latency:** ~25,258ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 34 |
| Pedagogy Failures | 51 |
| Helpfulness Failures | 59 |
| Domain Accuracy Failures | 33 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 4.00+ | 2 (lesson_01_derivatives, lesson_12_physics_newtons_law) |
| 3.50 – 3.99 | 6 (lesson_02_recursion, lesson_03_matrices, lesson_04_statistics, lesson_05_ml_basics, lesson_06_algebra, lesson_09_literature_themes) |
| 3.00 – 3.49 | 3 (lesson_07_physics_momentum, lesson_08_history_dates, lesson_11_programming_sort) |
| < 3.00 | 1 (lesson_10_chemistry_balancing) |

---

*Report auto-generated from 12 scored session files on 2026-03-12. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
