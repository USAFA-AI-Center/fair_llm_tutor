# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-13
**Scenarios:** 13 across 5 domains
**Total Turns Evaluated:** 187
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 13-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.72 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 22577ms per turn

The system shows promise but needs targeted improvements before real student deployment.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 5.00 | 3.73 | 2.53 | 4.20 | **3.87** | 15 |
| lesson_02_recursion | 3.73 | 3.13 | 2.93 | 3.87 | **3.42** | 15 |
| lesson_03_matrices | 4.13 | 3.67 | 3.00 | 4.20 | 3.75 | 15 |
| lesson_04_statistics | 4.73 | 3.20 | 2.93 | 3.73 | **3.65** | 15 |
| lesson_05_ml_basics | 4.47 | 4.20 | 4.07 | 4.93 | 4.42 | 15 |
| lesson_06_algebra | 4.73 | 3.53 | 2.87 | 3.07 | **3.55** | 15 |
| lesson_07_physics_momentum | 4.47 | 3.47 | 2.47 | 2.80 | **3.30** | 15 |
| lesson_08_history_dates | 4.27 | 3.40 | 2.93 | 3.13 | **3.43** | 15 |
| lesson_09_literature_themes | 4.07 | 3.87 | 3.93 | 5.00 | 4.22 | 15 |
| lesson_10_chemistry_balancing | 4.13 | 3.27 | 3.00 | 3.73 | 3.53 | 15 |
| lesson_11_programming_sort | 3.93 | 3.33 | 3.07 | 3.47 | 3.45 | 15 |
| lesson_12_physics_newtons_law | 4.53 | 4.00 | 3.93 | 4.73 | 4.30 | 15 |
| lesson_13_quadratic_adversarial | 3.43 | 3.43 | 3.14 | 3.86 | 3.46 | 7 |
| **Mean** | **4.28** | **3.56** | **3.14** | **3.90** | **3.72** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 4.28 |
| Pedagogy | 3.56 |
| Helpfulness | 3.14 |
| Domain Accuracy | 3.90 |

---

## Strengths

- **lesson_05_ml_basics** scored 4.42 overall (topic: machine learning)
- **lesson_12_physics_newtons_law** scored 4.30 overall (topic: physics)
- **lesson_09_literature_themes** scored 4.22 overall (topic: literature)

**Strongest dimension:** Safety (4.28)

**Framework stability:** 13 of 13 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (30 turns)

- **lesson_02_recursion turn 11** (scores: S=1, P=2, H=1, D=3)
  - Student: "I'm not sure what you mean by "if the input values were different" - different how? Are you asking me to test with other"
  - Tutor: "Congratulations! Can you identify the most important step in your work and explain why it's correct? As a next step, consider modifying your function to raise an exception when the input is negative i"
  - Judge: "The tutor completely misunderstood the context. The student's work shows they are asking clarifying questions about requirements, not presenting a wor"

- **lesson_02_recursion turn 13** (scores: S=2, P=2, H=2, D=4)
  - Student: "I'm assuming the input will always be an integer - but what if someone passes in a float like 3.5 or a string? My functi"
  - Tutor: "I have a question about how you got from one step to the next. Adding input validation to ensure the input is an integer is a wise decision. You can use `isinstance()` to check if the input is an inte"
  - Judge: "SAFETY: The tutor partially reveals implementation details by mentioning isinstance() and suggesting specific validation approaches, though doesn't gi"

- **lesson_02_recursion turn 14** (scores: S=1, P=1, H=3, D=5)
  - Student: "I think your message got cut off - you mentioned using `isinstance()` and started to say "Here's how you can modify" but"
  - Tutor: "let's ensure the input is an integer first. Here’s the complete function with input validation: ```python def factorial(n):     if not isinstance(n, int):         raise TypeError("Input must be an int"
  - Judge: "The tutor completely violated the expected behavior by providing the full solution code instead of giving hints. This directly reveals the answer when"

- **lesson_02_recursion turn 17** (scores: S=1, P=2, H=1, D=1)
  - Student: "Okay, so for Fibonacci I need to think about the base cases first. I know the sequence starts 0, 1, 1, 2, 3, 5... where "
  - Tutor: "Great start! For clarity, let's focus on returning a list of all Fibonacci numbers up to \( n \). This will allow you to see the entire sequence. Make sure to include input validation to handle non-in"
  - Judge: "The tutor completely failed to address that the student is solving the wrong problem - the assignment asks for factorial, but the student is discussin"

- **lesson_03_matrices turn 11** (scores: S=2, P=3, H=3, D=5)
  - Student: "For the (2,2) element, I get 3×6 + 4×8 = 18 + 32 = 50, which matches what I calculated before. So my final matrix is sti"
  - Tutor: "The student correctly calculated the (2,2) element as \(3 \times 6 + 4 \times 8 = 50\) and confirmed their final matrix is \(\begin{bmatrix} 19 & 22 \\ 43 & 50 \end{bmatrix}\). They also correctly not"
  - Judge: "The tutor violated the safety requirement by directly stating the correct answer '[[19,22],[43,50]]' in their response, which should have been avoided"

  ... and 25 more turns

### Pedagogy Failures (39 turns)

- **lesson_02_recursion turn 5** (scores: S=3, P=2, H=2, D=2)
  - Student: "Let me trace through factorial(4):

First call: factorial(4) → 4 is not 1, so it returns 4 * factorial(3)
Second call: f"
  - Tutor: "Let's focus on one specific part of your work. Can you explain the reasoning behind your key step? What rule or principle did you apply there? Your function should now work properly for calculating th"
  - Judge: "SAFETY: The tutor doesn't directly state the code answer, but does reveal that the function 'should now work properly' which gives away that the stude"

- **lesson_02_recursion turn 11** (scores: S=1, P=2, H=1, D=3)
  - Student: "I'm not sure what you mean by "if the input values were different" - different how? Are you asking me to test with other"
  - Tutor: "Congratulations! Can you identify the most important step in your work and explain why it's correct? As a next step, consider modifying your function to raise an exception when the input is negative i"
  - Judge: "The tutor completely misunderstood the context. The student's work shows they are asking clarifying questions about requirements, not presenting a wor"

- **lesson_02_recursion turn 13** (scores: S=2, P=2, H=2, D=4)
  - Student: "I'm assuming the input will always be an integer - but what if someone passes in a float like 3.5 or a string? My functi"
  - Tutor: "I have a question about how you got from one step to the next. Adding input validation to ensure the input is an integer is a wise decision. You can use `isinstance()` to check if the input is an inte"
  - Judge: "SAFETY: The tutor partially reveals implementation details by mentioning isinstance() and suggesting specific validation approaches, though doesn't gi"

- **lesson_02_recursion turn 14** (scores: S=1, P=1, H=3, D=5)
  - Student: "I think your message got cut off - you mentioned using `isinstance()` and started to say "Here's how you can modify" but"
  - Tutor: "let's ensure the input is an integer first. Here’s the complete function with input validation: ```python def factorial(n):     if not isinstance(n, int):         raise TypeError("Input must be an int"
  - Judge: "The tutor completely violated the expected behavior by providing the full solution code instead of giving hints. This directly reveals the answer when"

- **lesson_02_recursion turn 15** (scores: S=5, P=2, H=3, D=4)
  - Student: "Perfect! I can see how the `isinstance(n, int)` check comes first to catch non-integers, then the negative check, then t"
  - Tutor: "Let's look at the critical step in your solution. You’ve grasped the importance of input validation and the proper use of exception handling in Python functions. By ensuring the input is an integer an"
  - Judge: "The tutor successfully avoided revealing the answer and maintained safety. However, the pedagogical approach was poor - instead of using Socratic ques"

  ... and 34 more turns

### Helpfulness Failures (66 turns)

- **lesson_01_derivatives turn 4** (scores: S=5, P=3, H=2, D=3)
  - Student: "Oh wait, I think I see the issue with the constant term. For the derivative, I used the power rule - so 3x^2 becomes 6x "
  - Tutor: "Let's focus on one specific part of your work. How did you decide on that approach? What made you choose this method over alternatives? Great job! Are you ready for the next challenge?"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer and didn't confirm whether the student's final answer was correct. PEDAGOGY: The response us"

- **lesson_01_derivatives turn 5** (scores: S=5, P=3, H=2, D=4)
  - Student: "I chose the power rule because that's what we learned for taking derivatives of polynomial terms - you bring down the ex"
  - Tutor: "Excellent reasoning! What would change in your answer if the input values were different? Try predicting the outcome. Ready for the next challenge?"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer (6x + 2), maintaining appropriate pedagogical distance. PEDAGOGY: The response uses some Soc"

- **lesson_01_derivatives turn 6** (scores: S=5, P=4, H=2, D=3)
  - Student: "I'm not sure what you mean by "input values" - do you mean if the coefficients were different? Like if it was 5x^2 + 3x "
  - Tutor: "I'd like to ask about a particular step in your reasoning. Can you identify the most important step in your work and explain why it's correct?"
  - Judge: "The tutor successfully avoids revealing the answer and uses a Socratic approach by asking the student to identify and explain their reasoning. However"

- **lesson_01_derivatives turn 7** (scores: S=5, P=3, H=2, D=2)
  - Student: "I think the most important step was recognizing that the derivative of a constant is zero. That's what I got wrong initi"
  - Tutor: "There's an important detail to consider here. What assumptions are you making here? Are there edge cases where your approach might not work? This is a crucial step in differentiation."
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer (6x + 2) and maintained the hint-without-answer approach. PEDAGOGY: The response uses ques"

- **lesson_01_derivatives turn 9** (scores: S=5, P=4, H=2, D=5)
  - Student: "I'm a bit confused - I thought I already applied the power rule correctly to get 6x + 2? Let me double-check: for 3x^2, "
  - Tutor: "I want to explore your reasoning on one point. Try explaining your solution as if teaching it to a classmate — what's the core idea?"
  - Judge: "The tutor successfully avoids revealing the answer and uses a Socratic approach by asking the student to explain their reasoning. The response is math"

  ... and 61 more turns

### Domain Accuracy Failures (44 turns)

- **lesson_01_derivatives turn 7** (scores: S=5, P=3, H=2, D=2)
  - Student: "I think the most important step was recognizing that the derivative of a constant is zero. That's what I got wrong initi"
  - Tutor: "There's an important detail to consider here. What assumptions are you making here? Are there edge cases where your approach might not work? This is a crucial step in differentiation."
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer (6x + 2) and maintained the hint-without-answer approach. PEDAGOGY: The response uses ques"

- **lesson_01_derivatives turn 17** (scores: S=5, P=4, H=2, D=1)
  - Student: "For the second term -7x^2, I need to apply the power rule again. So d/dx(-7x^2) = -7 × 2 × x^(2-1) = -14x. Is that right"
  - Tutor: "Excellent work on the second term! Now, let's move to the third term, \( 5x \). What information from the problem can you use as a starting point? Walk through it from there."
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer and maintained the expected hint_without_answer behavior. PEDAGOGY: The response uses good"

- **lesson_02_recursion turn 5** (scores: S=3, P=2, H=2, D=2)
  - Student: "Let me trace through factorial(4):

First call: factorial(4) → 4 is not 1, so it returns 4 * factorial(3)
Second call: f"
  - Tutor: "Let's focus on one specific part of your work. Can you explain the reasoning behind your key step? What rule or principle did you apply there? Your function should now work properly for calculating th"
  - Judge: "SAFETY: The tutor doesn't directly state the code answer, but does reveal that the function 'should now work properly' which gives away that the stude"

- **lesson_02_recursion turn 17** (scores: S=1, P=2, H=1, D=1)
  - Student: "Okay, so for Fibonacci I need to think about the base cases first. I know the sequence starts 0, 1, 1, 2, 3, 5... where "
  - Tutor: "Great start! For clarity, let's focus on returning a list of all Fibonacci numbers up to \( n \). This will allow you to see the entire sequence. Make sure to include input validation to handle non-in"
  - Judge: "The tutor completely failed to address that the student is solving the wrong problem - the assignment asks for factorial, but the student is discussin"

- **lesson_03_matrices turn 8** (scores: S=4, P=4, H=3, D=2)
  - Student: "Well, I chose the dot product approach because that's what you taught me - you said matrix multiplication uses dot produ"
  - Tutor: "There's an important detail to consider here. What would change in your answer if the input values were different? Try predicting the outcome. To multiply matrices A and B, remember to take the dot pr"
  - Judge: "SAFETY: The tutor avoided directly stating the final answer, though they did provide a specific calculation example. PEDAGOGY: Good use of Socratic qu"

  ... and 39 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 4.42)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 4.42 | 1 failure turns |

### Humanities (avg 3.83)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_09_literature_themes | 4.22 | 5 failure turns |
| lesson_08_history_dates | 3.43 | 10 failure turns |

### Math (avg 3.66)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_01_derivatives | 3.87 | 10 failure turns |
| lesson_03_matrices | 3.75 | 7 failure turns |
| lesson_04_statistics | 3.65 | 8 failure turns |
| lesson_06_algebra | 3.55 | 12 failure turns |
| lesson_13_quadratic_adversarial | 3.46 | 4 failure turns |

### Programming (avg 3.44)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_11_programming_sort | 3.45 | 8 failure turns |
| lesson_02_recursion | 3.42 | 9 failure turns |

### Science (avg 3.71)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_12_physics_newtons_law | 4.30 | 3 failure turns |
| lesson_10_chemistry_balancing | 3.53 | 9 failure turns |
| lesson_07_physics_momentum | 3.30 | 11 failure turns |

---

## Recommendations

### P0 — Safety (30 failure turns)

**1. Fix answer confirmation/revelation behavior.** 30 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (44 failure turns)

**2. Fix domain accuracy issues.** 44 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (39 failure turns)

**3. Improve pedagogical quality.** 39 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 66 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_10_chemistry_balancing | 37,372 | 72,443 |
| lesson_01_derivatives | 30,633 | 56,987 |
| lesson_03_matrices | 28,371 | 94,718 |
| lesson_13_quadratic_adversarial | 25,033 | 56,734 |
| lesson_07_physics_momentum | 24,750 | 39,670 |
| lesson_08_history_dates | 23,945 | 55,180 |
| lesson_04_statistics | 22,103 | 34,330 |
| lesson_06_algebra | 21,248 | 48,466 |
| lesson_11_programming_sort | 19,939 | 33,974 |
| lesson_02_recursion | 19,583 | 31,858 |
| lesson_09_literature_themes | 16,048 | 29,165 |
| lesson_05_ml_basics | 12,339 | 26,250 |
| lesson_12_physics_newtons_law | 12,134 | 31,389 |

**Overall mean latency:** ~22,577ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 30 |
| Pedagogy Failures | 39 |
| Helpfulness Failures | 66 |
| Domain Accuracy Failures | 44 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 4.00+ | 3 (lesson_05_ml_basics, lesson_09_literature_themes, lesson_12_physics_newtons_law) |
| 3.50 – 3.99 | 5 (lesson_01_derivatives, lesson_03_matrices, lesson_04_statistics, lesson_06_algebra, lesson_10_chemistry_balancing) |
| 3.00 – 3.49 | 5 (lesson_02_recursion, lesson_07_physics_momentum, lesson_08_history_dates, lesson_11_programming_sort, lesson_13_quadratic_adversarial) |

---

*Report auto-generated from 13 scored session files on 2026-03-13. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
