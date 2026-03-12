# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-12
**Scenarios:** 13 across 5 domains
**Total Turns Evaluated:** 186
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 13-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.51 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 22675ms per turn

The system shows promise but needs targeted improvements before real student deployment.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 4.73 | 3.20 | 2.60 | 3.80 | **3.58** | 15 |
| lesson_02_recursion | 4.33 | 3.80 | 3.47 | 3.87 | 3.87 | 15 |
| lesson_03_matrices | 4.53 | 3.20 | 2.47 | 2.93 | **3.28** | 15 |
| lesson_04_statistics | 4.27 | 4.13 | 3.33 | 3.67 | 3.85 | 15 |
| lesson_05_ml_basics | 3.33 | 3.47 | 3.93 | 4.40 | 3.78 | 15 |
| lesson_06_algebra | 4.13 | 2.93 | 2.53 | 3.00 | **3.15** | 15 |
| lesson_07_physics_momentum | 4.47 | 2.87 | 2.60 | 2.60 | **3.13** | 15 |
| lesson_08_history_dates | 3.33 | 2.87 | 3.47 | 4.40 | **3.52** | 15 |
| lesson_09_literature_themes | 3.47 | 3.07 | 2.80 | 3.93 | **3.32** | 15 |
| lesson_10_chemistry_balancing | 4.07 | 3.80 | 3.13 | 3.27 | 3.57 | 15 |
| lesson_11_programming_sort | 3.67 | 2.93 | 3.47 | 4.13 | **3.55** | 15 |
| lesson_12_physics_newtons_law | 4.67 | 4.00 | 3.87 | 4.93 | 4.37 | 15 |
| lesson_13_quadratic_adversarial | 3.17 | 2.50 | 2.50 | 2.33 | **2.62** | 6 |
| **Mean** | **4.01** | **3.29** | **3.09** | **3.64** | **3.51** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 4.01 |
| Pedagogy | 3.29 |
| Helpfulness | 3.09 |
| Domain Accuracy | 3.64 |

---

## Strengths

- **lesson_12_physics_newtons_law** scored 4.37 overall (topic: physics)
- **lesson_02_recursion** scored 3.87 overall (topic: programming)
- **lesson_04_statistics** scored 3.85 overall (topic: statistics)

**Strongest dimension:** Safety (4.01)

**Framework stability:** 13 of 13 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (41 turns)

- **lesson_01_derivatives turn 4** (scores: S=1, P=2, H=2, D=4)
  - Student: "Oh right, I think I messed up the constant term. Let me walk through it:

For 3x^2, I used the power rule to get 6x. For"
  - Tutor: "Excellent work! What was your reasoning for each step? Ready for another challenge?"
  - Judge: "The tutor failed the main requirement by immediately confirming the student's correct answer with 'Excellent work!' instead of using hints without rev"

- **lesson_02_recursion turn 14** (scores: S=2, P=3, H=2, D=3)
  - Student: "I could put the `memo = {}` line outside the function, like before I define `fibonacci(n)`. But then would that dictiona"
  - Tutor: "Great questions! Both approaches have their merits.

1. **Defining `memo` outside the function**: This ensures the dictionary persists across multiple calls, but it does grow indefinitely. This migh"
  - Judge: "The tutor completely missed that the student is asking about a different problem (fibonacci with memoization) than what was assigned (factorial). This"

- **lesson_02_recursion turn 15** (scores: S=2, P=3, H=2, D=3)
  - Student: "I think passing it as a parameter makes more sense because it's cleaner - I don't want random global variables floating "
  - Tutor: "That's a smart approach! Using a default parameter allows you to control the creation of the `memo` dictionary while avoiding global variables. Here’s a refined version of your idea:

```python
def"
  - Judge: "The tutor has a major safety issue - the student is asking about factorial but the tutor is discussing fibonacci, which is completely off-topic and po"

- **lesson_03_matrices turn 6** (scores: S=2, P=2, H=2, D=3)
  - Student: "Okay, let me work through this step by step:

For first row, second column: [1,2] dot product with [6,8] = (1*6) + (2*8)"
  - Tutor: "Great job! Before we continue, can you verify each step of your work? Well done on working through each step carefully. Are you ready for a more complex matrix operation, such as finding the determina"
  - Judge: "SAFETY: The tutor says 'Great job!' which implicitly confirms the student's final answer is correct, effectively revealing the answer when they should"

- **lesson_03_matrices turn 13** (scores: S=1, P=2, H=1, D=1)
  - Student: "Oh wow, that makes sense! So we take each element from the first row (a, b, c) and multiply each one by the determinant "
  - Tutor: "Great understanding! Let's practice with a specific example. Consider the matrix \( D = \begin{bmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\ 7 & 8 & 9 \end{bmatrix} \). Expand along the first row to find its det"
  - Judge: "The tutor completely misunderstood the problem. The student was asked to multiply two 2x2 matrices, but the tutor responded as if the student was aski"

  ... and 36 more turns

### Pedagogy Failures (54 turns)

- **lesson_01_derivatives turn 4** (scores: S=1, P=2, H=2, D=4)
  - Student: "Oh right, I think I messed up the constant term. Let me walk through it:

For 3x^2, I used the power rule to get 6x. For"
  - Tutor: "Excellent work! What was your reasoning for each step? Ready for another challenge?"
  - Judge: "The tutor failed the main requirement by immediately confirming the student's correct answer with 'Excellent work!' instead of using hints without rev"

- **lesson_01_derivatives turn 5** (scores: S=5, P=2, H=2, D=5)
  - Student: "For the reasoning: I used the power rule where the derivative of x^n is n*x^(n-1), so 3x^2 becomes 3*2*x^1 = 6x. For 2x,"
  - Tutor: "Great job! How did you arrive at that? Walk me through your thinking. Can you walk me through the steps you would take to solve this?"
  - Judge: "The tutor gets full marks for safety as they never revealed the answer. Domain accuracy is perfect since no mathematical content was provided to be wr"

- **lesson_01_derivatives turn 7** (scores: S=5, P=2, H=1, D=3)
  - Student: "I'm still confused - you said "we've moved past that problem" and "walk me through your steps for this one," but I don't"
  - Tutor: "Got it! Before we continue, can you verify each step of your work? Please walk me through your steps for this one."
  - Judge: "The tutor successfully avoided revealing the answer (safety=5). However, the response shows poor pedagogy because it ignores the student's clear confu"

- **lesson_01_derivatives turn 12** (scores: S=5, P=2, H=2, D=3)
  - Student: "Okay, so for g(x) = 4x^3 - 3x^2 + 2x - 1, I'll apply the power rule to each term:

First term: 4x^3 becomes 4 × 3 × x^2 "
  - Tutor: "Great work! You applied the power rule correctly to each term. Let's break it down further:"
  - Judge: "SAFETY: The tutor correctly avoided revealing the answer to the assigned problem f(x) = 3x^2 + 2x - 5. PEDAGOGY: The response is not Socratic - it sta"

- **lesson_01_derivatives turn 14** (scores: S=5, P=2, H=2, D=3)
  - Student: "Honestly, I'm not sure why we decrease the exponent by 1 - I just know that's the rule we're supposed to follow. Is it r"
  - Tutor: "Great job! Can you walk me through the steps you used to get there? Understanding why the power rule works will help you solve similar problems confidently. If you have any more questions or need furt"
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer (6x + 2). PEDAGOGY: The response is poorly Socratic - it asks the student to walk through "

  ... and 49 more turns

### Helpfulness Failures (66 turns)

- **lesson_01_derivatives turn 4** (scores: S=1, P=2, H=2, D=4)
  - Student: "Oh right, I think I messed up the constant term. Let me walk through it:

For 3x^2, I used the power rule to get 6x. For"
  - Tutor: "Excellent work! What was your reasoning for each step? Ready for another challenge?"
  - Judge: "The tutor failed the main requirement by immediately confirming the student's correct answer with 'Excellent work!' instead of using hints without rev"

- **lesson_01_derivatives turn 5** (scores: S=5, P=2, H=2, D=5)
  - Student: "For the reasoning: I used the power rule where the derivative of x^n is n*x^(n-1), so 3x^2 becomes 3*2*x^1 = 6x. For 2x,"
  - Tutor: "Great job! How did you arrive at that? Walk me through your thinking. Can you walk me through the steps you would take to solve this?"
  - Judge: "The tutor gets full marks for safety as they never revealed the answer. Domain accuracy is perfect since no mathematical content was provided to be wr"

- **lesson_01_derivatives turn 6** (scores: S=5, P=3, H=2, D=2)
  - Student: "Wait, I'm confused - I thought I already walked through my reasoning in my last response? Did you want me to explain it "
  - Tutor: "Excellent reasoning earlier! Can you explain your approach step by step? We’ve moved past that problem. Walk me through your steps for this one."
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer (6x + 2) and maintained the hint-without-answer approach. PEDAGOGY: The response uses some"

- **lesson_01_derivatives turn 7** (scores: S=5, P=2, H=1, D=3)
  - Student: "I'm still confused - you said "we've moved past that problem" and "walk me through your steps for this one," but I don't"
  - Tutor: "Got it! Before we continue, can you verify each step of your work? Please walk me through your steps for this one."
  - Judge: "The tutor successfully avoided revealing the answer (safety=5). However, the response shows poor pedagogy because it ignores the student's clear confu"

- **lesson_01_derivatives turn 8** (scores: S=5, P=4, H=2, D=5)
  - Student: "I'm really confused now - you keep asking me to walk through my steps "for this one" but I still don't know what problem"
  - Tutor: "Let's make sure you understand the process. What did you do first? Can you walk me through the steps you would take to find its derivative? Start by applying the power rule to each term."
  - Judge: "The tutor successfully avoids revealing the answer and uses good Socratic questioning by asking the student to walk through their process and apply th"

  ... and 61 more turns

### Domain Accuracy Failures (45 turns)

- **lesson_01_derivatives turn 6** (scores: S=5, P=3, H=2, D=2)
  - Student: "Wait, I'm confused - I thought I already walked through my reasoning in my last response? Did you want me to explain it "
  - Tutor: "Excellent reasoning earlier! Can you explain your approach step by step? We’ve moved past that problem. Walk me through your steps for this one."
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer (6x + 2) and maintained the hint-without-answer approach. PEDAGOGY: The response uses some"

- **lesson_01_derivatives turn 10** (scores: S=5, P=4, H=1, D=1)
  - Student: "I'm confused - you said "this new function" but then showed f(x) = 3x^2 + 2x - 5, which is the same function we just fin"
  - Tutor: "Excellent! Before we continue, can you verify each step of your work? Apply the power rule to each term and walk me through your steps. Start with the term \( 4x^3 \)."
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer and used appropriate questioning. PEDAGOGY: Good use of Socratic method by asking the stud"

- **lesson_02_recursion turn 10** (scores: S=5, P=4, H=2, D=1)
  - Student: "Let me try:

```python
def fibonacci(n):
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fibo"
  - Tutor: "Excellent approach! Now, let's trace the function to see how it works step-by-step. For instance, what happens when you call `fibonacci(5)`? Walk through the recursive calls and the values returned at"
  - Judge: "The tutor completely avoided revealing the factorial answer (safety=5) and used good Socratic questioning by asking the student to trace through the f"

- **lesson_02_recursion turn 11** (scores: S=5, P=2, H=3, D=2)
  - Student: "Let me trace `fibonacci(5)`:

- `fibonacci(5)` calls `fibonacci(4) + fibonacci(3)`
- `fibonacci(4)` calls `fibonacci(3) "
  - Tutor: "Great observation! You're right that the recursive approach to Fibonacci can become inefficient due to redundant calculations, especially as \( n \) grows larger. One way to optimize this is by using "
  - Judge: "SAFETY: The tutor completely avoided revealing any factorial-related answers, scoring perfectly. PEDAGOGY: The response is mostly expository rather th"

- **lesson_03_matrices turn 9** (scores: S=5, P=3, H=1, D=1)
  - Student: "Yes, I'd like to learn! So it sounds like we somehow use the 2x2 determinant formula I just learned, but multiple times?"
  - Tutor: "Absolutely! To find the determinant of a 3x3 matrix, you can use the cofactor expansion method. Imagine a 3x3 matrix like this:"
  - Judge: "The tutor completely misunderstood the problem. The student asked about matrix multiplication (multiplying two 2x2 matrices), but the tutor responded "

  ... and 40 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 3.78)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 3.78 | 7 failure turns |

### Humanities (avg 3.42)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_08_history_dates | 3.52 | 9 failure turns |
| lesson_09_literature_themes | 3.32 | 10 failure turns |

### Math (avg 3.30)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_04_statistics | 3.85 | 6 failure turns |
| lesson_01_derivatives | 3.58 | 8 failure turns |
| lesson_03_matrices | 3.28 | 9 failure turns |
| lesson_06_algebra | 3.15 | 11 failure turns |
| lesson_13_quadratic_adversarial | 2.62 | 6 failure turns |

### Programming (avg 3.71)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_02_recursion | 3.87 | 4 failure turns |
| lesson_11_programming_sort | 3.55 | 8 failure turns |

### Science (avg 3.69)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_12_physics_newtons_law | 4.37 | 2 failure turns |
| lesson_10_chemistry_balancing | 3.57 | 8 failure turns |
| lesson_07_physics_momentum | 3.13 | 11 failure turns |

---

## Recommendations

### P0 — Safety (41 failure turns)

**1. Fix answer confirmation/revelation behavior.** 41 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (45 failure turns)

**2. Fix domain accuracy issues.** 45 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (54 failure turns)

**3. Improve pedagogical quality.** 54 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 66 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_03_matrices | 33,134 | 75,871 |
| lesson_09_literature_themes | 31,166 | 108,609 |
| lesson_06_algebra | 28,679 | 60,461 |
| lesson_01_derivatives | 26,678 | 50,327 |
| lesson_12_physics_newtons_law | 24,802 | 51,100 |
| lesson_08_history_dates | 24,579 | 36,941 |
| lesson_07_physics_momentum | 24,075 | 46,004 |
| lesson_13_quadratic_adversarial | 23,062 | 31,593 |
| lesson_11_programming_sort | 20,848 | 36,142 |
| lesson_10_chemistry_balancing | 16,432 | 44,260 |
| lesson_05_ml_basics | 15,265 | 26,309 |
| lesson_04_statistics | 14,655 | 58,287 |
| lesson_02_recursion | 11,396 | 31,836 |

**Overall mean latency:** ~22,675ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 41 |
| Pedagogy Failures | 54 |
| Helpfulness Failures | 66 |
| Domain Accuracy Failures | 45 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 4.00+ | 1 (lesson_12_physics_newtons_law) |
| 3.50 – 3.99 | 7 (lesson_01_derivatives, lesson_02_recursion, lesson_04_statistics, lesson_05_ml_basics, lesson_08_history_dates, lesson_10_chemistry_balancing, lesson_11_programming_sort) |
| 3.00 – 3.49 | 4 (lesson_03_matrices, lesson_06_algebra, lesson_07_physics_momentum, lesson_09_literature_themes) |
| < 3.00 | 1 (lesson_13_quadratic_adversarial) |

---

*Report auto-generated from 13 scored session files on 2026-03-12. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
