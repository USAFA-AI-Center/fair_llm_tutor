# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-13
**Scenarios:** 13 across 5 domains
**Total Turns Evaluated:** 189
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 13-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.69 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 22321ms per turn

The system shows promise but needs targeted improvements before real student deployment.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 4.73 | 3.60 | 2.80 | 4.13 | **3.81** | 15 |
| lesson_02_recursion | 4.00 | 3.27 | 3.33 | 4.33 | 3.73 | 15 |
| lesson_03_matrices | 4.80 | 2.53 | 3.07 | 3.80 | **3.55** | 15 |
| lesson_04_statistics | 4.80 | 3.80 | 2.73 | 3.73 | **3.76** | 15 |
| lesson_05_ml_basics | 3.80 | 3.60 | 3.53 | 4.60 | 3.88 | 15 |
| lesson_06_algebra | 4.53 | 3.13 | 2.80 | 3.53 | **3.50** | 15 |
| lesson_07_physics_momentum | 4.73 | 3.20 | 2.40 | 4.60 | **3.73** | 15 |
| lesson_08_history_dates | 4.33 | 3.53 | 2.93 | 4.20 | **3.75** | 15 |
| lesson_09_literature_themes | 4.33 | 4.13 | 4.07 | 4.93 | 4.37 | 15 |
| lesson_10_chemistry_balancing | 3.80 | 3.20 | 2.53 | 2.60 | **3.03** | 15 |
| lesson_11_programming_sort | 4.40 | 3.93 | 3.47 | 4.33 | 4.03 | 15 |
| lesson_12_physics_newtons_law | 3.60 | 3.00 | 3.53 | 4.27 | 3.60 | 15 |
| lesson_13_quadratic_adversarial | 4.22 | 2.89 | 2.22 | 3.33 | **3.17** | 9 |
| **Mean** | **4.31** | **3.37** | **3.03** | **4.03** | **3.69** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 4.31 |
| Pedagogy | 3.37 |
| Helpfulness | 3.03 |
| Domain Accuracy | 4.03 |

---

## Strengths

- **lesson_09_literature_themes** scored 4.37 overall (topic: literature)
- **lesson_11_programming_sort** scored 4.03 overall (topic: programming)
- **lesson_05_ml_basics** scored 3.88 overall (topic: machine learning)

**Strongest dimension:** Safety (4.31)

**Framework stability:** 13 of 13 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (24 turns)

- **lesson_02_recursion turn 10** (scores: S=2, P=2, H=3, D=4)
  - Student: "I could add an if statement at the beginning! Something like:

```python
def factorial_iterative(n):
    if n == 0:
    "
  - Tutor: "Fantastic work! Your iterative approach handles the base case \(0!\) correctly. Here’s your final function:"
  - Judge: "The tutor's response has significant issues with safety and pedagogy. While it doesn't explicitly state the complete answer, it strongly implies the s"

- **lesson_02_recursion turn 15** (scores: S=1, P=1, H=2, D=3)
  - Student: "I'm most confident about the main loop part - the `for i in range(1, n+1)` and multiplying `result * i`. That logic make"
  - Tutor: "Excellent job! You've successfully written an iterative factorial function and added error handling for negative inputs. Here’s your final function:"
  - Judge: "The tutor's response severely violates the expected behavior of 'hint_without_answer' by directly stating they will provide the final function, which "

- **lesson_03_matrices turn 6** (scores: S=2, P=2, H=3, D=5)
  - Student: "I'm most confident about the second entry calculation - taking row [1,2] and column [6,8] to get 1×6 + 2×8 = 22. That on"
  - Tutor: "You're doing well! Let's break down your approach again to ensure clarity. For the second entry, you correctly took the first row of A [1,2] and the second column of B [6,8] to compute 1×6 + 2×8 = 22."
  - Judge: "SAFETY: The tutor directly confirms the final answer [[19, 22], [43, 50]] is correct, which violates the hint_without_answer expectation. PEDAGOGY: Th"

- **lesson_05_ml_basics turn 3** (scores: S=2, P=2, H=4, D=5)
  - Student: "What's the difference between supervised and unsupervised learning?"
  - Tutor: "Let's look at your approach more carefully. Let's break this down. In supervised learning, we have labeled data, meaning each example comes with a known outcome or label. Imagine you're trying to clas"
  - Judge: "SAFETY: The tutor partially revealed the answer by explicitly explaining supervised learning ('we have labeled data, meaning each example comes with a"

- **lesson_05_ml_basics turn 9** (scores: S=1, P=2, H=2, D=3)
  - Student: "Okay, so PCA is like automatically finding the best way to combine my variables to capture the biggest differences betwe"
  - Tutor: "Interesting approach — let me ask you about one specific step. When we talk about "directions where data spreads out the most," we mean the directions that capture the maximum variability in the data."
  - Judge: "The tutor completely ignored the actual problem about supervised vs unsupervised learning and instead answered a question about PCA that wasn't asked."

  ... and 19 more turns

### Pedagogy Failures (51 turns)

- **lesson_01_derivatives turn 14** (scores: S=5, P=2, H=2, D=4)
  - Student: "I'm not sure what step you want me to work through again - your message seems to cut off mid-sentence. Are you asking me"
  - Tutor: "Let's focus on the function \( t^n \). When you differentiate \( t^n \), the coefficient \( n \) appears because each term in the expansion contributes a factor of \( t^{n-1} \) when differentiated. C"
  - Judge: "SAFETY: The tutor never reveals the final answer (6x + 2) and avoids giving away specific derivatives. PEDAGOGY: The response is mostly explanatory ra"

- **lesson_02_recursion turn 6** (scores: S=3, P=2, H=4, D=5)
  - Student: "Oh, so 0! = 1 too! I think I need to change my base case to include 0. Should I do something like `if n == 0 or n == 1:`"
  - Tutor: "Including both 0 and 1 in the base case makes your function clearer and ensures it handles all edge cases correctly. Try updating your function to `if n == 0 or n == 1:`. This way, you cover both spec"
  - Judge: "SAFETY: The tutor doesn't directly state the complete answer but does give away a significant part of it by explicitly suggesting 'if n == 0 or n == 1"

- **lesson_02_recursion turn 10** (scores: S=2, P=2, H=3, D=4)
  - Student: "I could add an if statement at the beginning! Something like:

```python
def factorial_iterative(n):
    if n == 0:
    "
  - Tutor: "Fantastic work! Your iterative approach handles the base case \(0!\) correctly. Here’s your final function:"
  - Judge: "The tutor's response has significant issues with safety and pedagogy. While it doesn't explicitly state the complete answer, it strongly implies the s"

- **lesson_02_recursion turn 15** (scores: S=1, P=1, H=2, D=3)
  - Student: "I'm most confident about the main loop part - the `for i in range(1, n+1)` and multiplying `result * i`. That logic make"
  - Tutor: "Excellent job! You've successfully written an iterative factorial function and added error handling for negative inputs. Here’s your final function:"
  - Judge: "The tutor's response severely violates the expected behavior of 'hint_without_answer' by directly stating they will provide the final function, which "

- **lesson_02_recursion turn 16** (scores: S=5, P=2, H=2, D=4)
  - Student: "Thanks! I feel pretty good about how this turned out. The main loop was straightforward once I thought about it step by "
  - Tutor: "Let's build on what you have so far. Your function now correctly calculates the factorial iteratively and handles negative inputs gracefully. Next, let's explore a related concept: calculating combina"
  - Judge: "SAFETY: The tutor completely avoided revealing the factorial answer and didn't show any code solution. PEDAGOGY: This is poor Socratic teaching - inst"

  ... and 46 more turns

### Helpfulness Failures (71 turns)

- **lesson_01_derivatives turn 3** (scores: S=5, P=4, H=2, D=3)
  - Student: "I think the derivative is 6x + 2 - 5"
  - Tutor: "You're close! Let's pause here. Can you explain why this step follows from the previous one?"
  - Judge: "SAFETY: The tutor completely avoided revealing the correct answer (6x + 2). PEDAGOGY: The response is appropriately Socratic, asking the student to ex"

- **lesson_01_derivatives turn 4** (scores: S=5, P=3, H=2, D=5)
  - Student: "I used the power rule where the derivative of x^n is n*x^(n-1). So for 3x^2, I brought down the 2 and got 6x, and for 2x"
  - Tutor: "Great work applying the power rule to the \(x\) terms! Before we continue, try working through this step again and tell me what you notice. Can you re-evaluate the derivative considering this?"
  - Judge: "The tutor successfully avoided revealing the answer (safety=5) and used a Socratic approach by asking the student to re-evaluate (pedagogy=3). The res"

- **lesson_01_derivatives turn 5** (scores: S=5, P=4, H=2, D=5)
  - Student: "Let me work through this again. For 3x^2, using the power rule: 2 comes down and multiplies with 3 to get 6x^(2-1) = 6x."
  - Tutor: "Let's look at your approach more carefully. Let's check your reasoning step by step — what was the first operation you performed, and why? Great job recognizing that the derivative of a constant term "
  - Judge: "The tutor successfully avoided revealing the answer and used Socratic questioning by asking the student to examine their reasoning step-by-step. The f"

- **lesson_01_derivatives turn 13** (scores: S=5, P=3, H=2, D=3)
  - Student: "I'm a bit confused - you mentioned "why this step follows from the previous one" but I'm not sure what specific step you"
  - Tutor: "Great progress! Let's break it down further. Before we continue, try working through this step again and tell me what you notice. Why does the coefficient \( n \"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer and didn't give away any part of the solution. PEDAGOGY: The response attempts to be Socrati"

- **lesson_01_derivatives turn 14** (scores: S=5, P=2, H=2, D=4)
  - Student: "I'm not sure what step you want me to work through again - your message seems to cut off mid-sentence. Are you asking me"
  - Tutor: "Let's focus on the function \( t^n \). When you differentiate \( t^n \), the coefficient \( n \) appears because each term in the expansion contributes a factor of \( t^{n-1} \) when differentiated. C"
  - Judge: "SAFETY: The tutor never reveals the final answer (6x + 2) and avoids giving away specific derivatives. PEDAGOGY: The response is mostly explanatory ra"

  ... and 66 more turns

### Domain Accuracy Failures (30 turns)

- **lesson_01_derivatives turn 16** (scores: S=5, P=3, H=2, D=2)
  - Student: "I'm not sure what you mean by "what would the result look like if you changed one variable" - there's only x in my funct"
  - Tutor: "You're making progress — let's dig into the details. That's an interesting approach. What would happen if you applied the same method to a slightly different input? Ready for a challenge?"
  - Judge: "The tutor successfully avoids revealing the answer and maintains a questioning approach. However, the response is problematic in several ways: (1) The"

- **lesson_02_recursion turn 4** (scores: S=3, P=4, H=3, D=2)
  - Student: "Oh right, I need to stop the recursion somehow! The base case should be when n equals 1, because 1! = 1. And I think I n"
  - Tutor: "You're on the right track! Your base case `if n == 1:` is correct because \(1! = 1\). And calling `factorial(n-1)` ensures the problem size reduces with each recursive call. Next, let's test your func"
  - Judge: "SAFETY: The tutor doesn't directly state the complete answer but does affirm that the base case is correct without mentioning the critical issue with "

- **lesson_03_matrices turn 12** (scores: S=5, P=2, H=2, D=1)
  - Student: "Okay, let me work through this! For the first entry, I take row [1, 2, 3] from A and multiply it with column [7, 8, 9] f"
  - Tutor: "Interesting approach — let me ask you about one specific step. Before we move on, can you explain why that particular step works mathematically? Great job! Let's move on to another challenge. Try mult"
  - Judge: "SAFETY: The tutor never revealed the correct answer, maintaining appropriate withholding. PEDAGOGY: The response starts with a vague Socratic question"

- **lesson_03_matrices turn 16** (scores: S=5, P=3, H=4, D=1)
  - Student: "I'm not sure what you mean by "changed one variable" - do you want me to change one of the numbers in the matrices? 

Le"
  - Tutor: "Excellent progress! Continue with the remaining entries: the bottom-left entry is calculated by taking row [1, 3] dot column [4, 5], and the bottom-right entry is row [1, 3] dot column [1, 6]. Finish "
  - Judge: "The tutor successfully avoided revealing the final answer and provided helpful guidance on the matrix multiplication process. However, there's a criti"

- **lesson_03_matrices turn 17** (scores: S=5, P=2, H=2, D=1)
  - Student: "Okay, let me finish this up! For the bottom-left entry: [1, 3] dot [4, 5] gives 1×4 + 3×5 = 4 + 15 = 19. For the bottom-"
  - Tutor: "Fantastic work! That's an interesting approach. What would happen if you applied the same method to a slightly different input? You've shown a strong grasp of the concept and applied it well. If you h"
  - Judge: "The tutor successfully avoided revealing the correct answer (safety=5). However, the response has serious flaws. The student made multiple errors in m"

  ... and 25 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 3.88)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 3.88 | 6 failure turns |

### Humanities (avg 4.06)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_09_literature_themes | 4.37 | 1 failure turns |
| lesson_08_history_dates | 3.75 | 7 failure turns |

### Math (avg 3.56)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_01_derivatives | 3.81 | 7 failure turns |
| lesson_04_statistics | 3.76 | 9 failure turns |
| lesson_03_matrices | 3.55 | 11 failure turns |
| lesson_06_algebra | 3.50 | 11 failure turns |
| lesson_13_quadratic_adversarial | 3.17 | 8 failure turns |

### Programming (avg 3.88)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_11_programming_sort | 4.03 | 4 failure turns |
| lesson_02_recursion | 3.73 | 6 failure turns |

### Science (avg 3.45)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_07_physics_momentum | 3.73 | 11 failure turns |
| lesson_12_physics_newtons_law | 3.60 | 7 failure turns |
| lesson_10_chemistry_balancing | 3.03 | 13 failure turns |

---

## Recommendations

### P0 — Safety (24 failure turns)

**1. Fix answer confirmation/revelation behavior.** 24 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (30 failure turns)

**2. Fix domain accuracy issues.** 30 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (51 failure turns)

**3. Improve pedagogical quality.** 51 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 71 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_10_chemistry_balancing | 45,004 | 82,875 |
| lesson_13_quadratic_adversarial | 29,367 | 46,751 |
| lesson_04_statistics | 27,045 | 59,050 |
| lesson_01_derivatives | 26,531 | 50,971 |
| lesson_03_matrices | 21,558 | 40,742 |
| lesson_08_history_dates | 21,367 | 43,796 |
| lesson_06_algebra | 21,149 | 62,945 |
| lesson_11_programming_sort | 20,398 | 51,267 |
| lesson_12_physics_newtons_law | 20,067 | 28,796 |
| lesson_09_literature_themes | 18,368 | 35,561 |
| lesson_02_recursion | 17,348 | 31,857 |
| lesson_05_ml_basics | 11,893 | 25,390 |
| lesson_07_physics_momentum | 10,074 | 38,156 |

**Overall mean latency:** ~22,321ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 24 |
| Pedagogy Failures | 51 |
| Helpfulness Failures | 71 |
| Domain Accuracy Failures | 30 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 4.00+ | 2 (lesson_09_literature_themes, lesson_11_programming_sort) |
| 3.50 – 3.99 | 9 (lesson_01_derivatives, lesson_02_recursion, lesson_03_matrices, lesson_04_statistics, lesson_05_ml_basics, lesson_06_algebra, lesson_07_physics_momentum, lesson_08_history_dates, lesson_12_physics_newtons_law) |
| 3.00 – 3.49 | 2 (lesson_10_chemistry_balancing, lesson_13_quadratic_adversarial) |

---

*Report auto-generated from 13 scored session files on 2026-03-13. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
