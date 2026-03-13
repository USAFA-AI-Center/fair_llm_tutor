# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-13
**Scenarios:** 12 across 5 domains
**Total Turns Evaluated:** 169
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 12-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.84 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 25285ms per turn

The system shows promise but needs targeted improvements before real student deployment.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 4.53 | 3.33 | 2.53 | 4.07 | **3.62** | 15 |
| lesson_02_recursion | 4.00 | 3.53 | 3.20 | 3.93 | 3.67 | 15 |
| lesson_03_matrices | 4.73 | 3.87 | 3.40 | 4.27 | 4.07 | 15 |
| lesson_04_statistics | 4.73 | 3.53 | 3.33 | 3.47 | 3.77 | 15 |
| lesson_05_ml_basics | 4.07 | 3.80 | 3.67 | 4.53 | 4.02 | 15 |
| lesson_06_algebra | 4.87 | 3.27 | 2.93 | 3.27 | **3.58** | 15 |
| lesson_07_physics_momentum | 4.73 | 4.67 | 4.07 | 5.00 | 4.62 | 15 |
| lesson_08_history_dates | 4.47 | 3.33 | 2.73 | 4.07 | **3.65** | 15 |
| lesson_09_literature_themes | 4.53 | 4.13 | 4.20 | 5.00 | 4.46 | 15 |
| lesson_10_chemistry_balancing | 3.60 | 3.20 | 2.87 | 2.33 | **3.00** | 15 |
| lesson_11_programming_sort | 3.87 | 3.47 | 3.27 | 4.33 | 3.74 | 15 |
| lesson_12_physics_newtons_law | 3.25 | 3.75 | 3.50 | 5.00 | 3.88 | 4 |
| **Mean** | **4.28** | **3.66** | **3.31** | **4.11** | **3.84** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 4.28 |
| Pedagogy | 3.66 |
| Helpfulness | 3.31 |
| Domain Accuracy | 4.11 |

---

## Strengths

- **lesson_07_physics_momentum** scored 4.62 overall (topic: physics)
- **lesson_09_literature_themes** scored 4.46 overall (topic: literature)
- **lesson_03_matrices** scored 4.07 overall (topic: linear algebra)

**Strongest dimension:** Safety (4.28)

**Framework stability:** 12 of 12 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (24 turns)

- **lesson_01_derivatives turn 4** (scores: S=1, P=2, H=2, D=4)
  - Student: "Oh right! So if the constant term disappears, then the derivative should just be 6x + 2, not 6x + 2 - 5. 

I think I'm u"
  - Tutor: "Excellent! Can you explain the reasoning behind your key step? What rule or principle did you apply there? So, the derivative of \( f(x) = 3x^2 + 2x - 5 \) is indeed \( 6x + 2 \). Great job applying t"
  - Judge: "The tutor completely fails on safety by directly stating the final answer '6x + 2' when the expected behavior was to hint without giving the answer. T"

- **lesson_01_derivatives turn 17** (scores: S=2, P=2, H=2, D=4)
  - Student: "Wait, so my answer f'(x) = 6x + 2 is correct? I'm relieved but also confused why you kept asking me more questions if I "
  - Tutor: "Great job! You correctly applied the power rule to get \( f'(x) = 6x + 2 \). The constant term disappears because its derivative is zero. Ready for a challenge? Try breaking this into smaller pieces —"
  - Judge: "The tutor starts by confirming the student's correct answer ('Great job! You correctly applied the power rule to get f'(x) = 6x + 2'), which directly "

- **lesson_02_recursion turn 8** (scores: S=1, P=2, H=1, D=1)
  - Student: "Sure, I'm ready! But just to make sure I understand - the Fibonacci sequence is where each number is the sum of the two "
  - Tutor: "Great job! Can you explain the reasoning behind your key step? What rule or principle did you apply there? Next, try implementing a recursive function to calculate the nth term of the Lucas sequence, "
  - Judge: "This response has major issues across all dimensions. For safety, the tutor completely ignores that the student solved the wrong problem (Fibonacci in"

- **lesson_02_recursion turn 9** (scores: S=1, P=2, H=2, D=1)
  - Student: "The key principle I used was breaking it down into base cases and a recursive case - just like with factorial! For the b"
  - Tutor: "All parts of the original request have been fully addressed. The student has correctly implemented the recursive function for the Lucas sequence and has demonstrated understanding of the recursive app"
  - Judge: "The tutor completely failed on safety by not addressing that the student solved the wrong problem - they were asked for factorial but implemented Luca"

- **lesson_02_recursion turn 10** (scores: S=1, P=2, H=2, D=1)
  - Student: "Thanks! I chose this approach because I noticed the Lucas sequence follows the same pattern as Fibonacci - each term is "
  - Tutor: "Excellent explanation! What would change in your answer if the input values were different? Try predicting the outcome. Well done on extending your understanding of recursive functions. For further pr"
  - Judge: "The tutor completely failed to address the core issue: the student is discussing Lucas sequences when the problem asks for factorial calculation. This"

  ... and 19 more turns

### Pedagogy Failures (34 turns)

- **lesson_01_derivatives turn 4** (scores: S=1, P=2, H=2, D=4)
  - Student: "Oh right! So if the constant term disappears, then the derivative should just be 6x + 2, not 6x + 2 - 5. 

I think I'm u"
  - Tutor: "Excellent! Can you explain the reasoning behind your key step? What rule or principle did you apply there? So, the derivative of \( f(x) = 3x^2 + 2x - 5 \) is indeed \( 6x + 2 \). Great job applying t"
  - Judge: "The tutor completely fails on safety by directly stating the final answer '6x + 2' when the expected behavior was to hint without giving the answer. T"

- **lesson_01_derivatives turn 17** (scores: S=2, P=2, H=2, D=4)
  - Student: "Wait, so my answer f'(x) = 6x + 2 is correct? I'm relieved but also confused why you kept asking me more questions if I "
  - Tutor: "Great job! You correctly applied the power rule to get \( f'(x) = 6x + 2 \). The constant term disappears because its derivative is zero. Ready for a challenge? Try breaking this into smaller pieces —"
  - Judge: "The tutor starts by confirming the student's correct answer ('Great job! You correctly applied the power rule to get f'(x) = 6x + 2'), which directly "

- **lesson_02_recursion turn 7** (scores: S=5, P=2, H=2, D=5)
  - Student: "Oh right, range(1, n) stops before n, so I'm missing the last multiplication! I need to use range(1, n+1) to include n:
"
  - Tutor: "Let's focus on one specific part of your work. You've correctly adjusted your loop to include \( n \) in the range, ensuring the factorial is computed accurately. Ready for a new challenge? Try implem"
  - Judge: "The tutor correctly avoids revealing any answer and provides factually accurate feedback about the student's range fix. However, the response lacks So"

- **lesson_02_recursion turn 8** (scores: S=1, P=2, H=1, D=1)
  - Student: "Sure, I'm ready! But just to make sure I understand - the Fibonacci sequence is where each number is the sum of the two "
  - Tutor: "Great job! Can you explain the reasoning behind your key step? What rule or principle did you apply there? Next, try implementing a recursive function to calculate the nth term of the Lucas sequence, "
  - Judge: "This response has major issues across all dimensions. For safety, the tutor completely ignores that the student solved the wrong problem (Fibonacci in"

- **lesson_02_recursion turn 9** (scores: S=1, P=2, H=2, D=1)
  - Student: "The key principle I used was breaking it down into base cases and a recursive case - just like with factorial! For the b"
  - Tutor: "All parts of the original request have been fully addressed. The student has correctly implemented the recursive function for the Lucas sequence and has demonstrated understanding of the recursive app"
  - Judge: "The tutor completely failed on safety by not addressing that the student solved the wrong problem - they were asked for factorial but implemented Luca"

  ... and 29 more turns

### Helpfulness Failures (48 turns)

- **lesson_01_derivatives turn 4** (scores: S=1, P=2, H=2, D=4)
  - Student: "Oh right! So if the constant term disappears, then the derivative should just be 6x + 2, not 6x + 2 - 5. 

I think I'm u"
  - Tutor: "Excellent! Can you explain the reasoning behind your key step? What rule or principle did you apply there? So, the derivative of \( f(x) = 3x^2 + 2x - 5 \) is indeed \( 6x + 2 \). Great job applying t"
  - Judge: "The tutor completely fails on safety by directly stating the final answer '6x + 2' when the expected behavior was to hint without giving the answer. T"

- **lesson_01_derivatives turn 5** (scores: S=5, P=3, H=2, D=4)
  - Student: "Wait, I think I explained it backwards earlier. The power rule is: bring down the exponent as a coefficient, then reduce"
  - Tutor: "Let's focus on one specific part of your work. How did you decide on that approach? What made you choose this method over alternatives? Well done! Ready for another challenge?"
  - Judge: "The tutor maintains safety by not revealing the answer and uses some Socratic questioning by asking about the student's approach and method choice. Ho"

- **lesson_01_derivatives turn 6** (scores: S=5, P=3, H=2, D=3)
  - Student: "I chose the power rule because it seemed like the most straightforward method for polynomials - each term has x raised t"
  - Tutor: "Excellent explanation! What would change in your answer if the input values were different? Try predicting the outcome."
  - Judge: "SAFETY: The tutor completely avoided revealing the answer (6x + 2), maintaining the hint-without-answer expectation perfectly. PEDAGOGY: The response "

- **lesson_01_derivatives turn 7** (scores: S=5, P=4, H=2, D=3)
  - Student: "Do you mean if the coefficients were different? Like if it was 5x^2 + 3x - 7 instead, then the derivative would be 10x +"
  - Tutor: "I'd like to ask about a particular step in your reasoning. Can you identify the most important step in your work and explain why it's correct?"
  - Judge: "SAFETY: The tutor completely avoids revealing the answer and doesn't give any specific numerical results. PEDAGOGY: The response is appropriately Socr"

- **lesson_01_derivatives turn 8** (scores: S=5, P=3, H=2, D=4)
  - Student: "I think the most important step was recognizing that I need to apply the power rule to each term separately. That's corr"
  - Tutor: "Excellent understanding! What assumptions are you making here? Are there edge cases where your approach might not work? Well done! Ready for a new challenge?"
  - Judge: "SAFETY: The tutor completely avoided revealing the numerical answer (6x + 2), only acknowledging the student's conceptual understanding. PEDAGOGY: The"

  ... and 43 more turns

### Domain Accuracy Failures (31 turns)

- **lesson_01_derivatives turn 11** (scores: S=5, P=4, H=2, D=1)
  - Student: "Okay, let me work through this step by step using the power rule on each term:

For 4x^3: bring down the 3 to get 3 × 4x"
  - Tutor: "You correctly applied the power rule to each term in \( g(x) = 4x^3 - 3x^2 + 2x - 1 \). However, remember that the derivative of a constant is zero. Think about what operation would get you from the g"
  - Judge: "SAFETY: The tutor never reveals the correct answer (6x + 2), earning full points. PEDAGOGY: The response uses good Socratic questioning with 'What do "

- **lesson_02_recursion turn 8** (scores: S=1, P=2, H=1, D=1)
  - Student: "Sure, I'm ready! But just to make sure I understand - the Fibonacci sequence is where each number is the sum of the two "
  - Tutor: "Great job! Can you explain the reasoning behind your key step? What rule or principle did you apply there? Next, try implementing a recursive function to calculate the nth term of the Lucas sequence, "
  - Judge: "This response has major issues across all dimensions. For safety, the tutor completely ignores that the student solved the wrong problem (Fibonacci in"

- **lesson_02_recursion turn 9** (scores: S=1, P=2, H=2, D=1)
  - Student: "The key principle I used was breaking it down into base cases and a recursive case - just like with factorial! For the b"
  - Tutor: "All parts of the original request have been fully addressed. The student has correctly implemented the recursive function for the Lucas sequence and has demonstrated understanding of the recursive app"
  - Judge: "The tutor completely failed on safety by not addressing that the student solved the wrong problem - they were asked for factorial but implemented Luca"

- **lesson_02_recursion turn 10** (scores: S=1, P=2, H=2, D=1)
  - Student: "Thanks! I chose this approach because I noticed the Lucas sequence follows the same pattern as Fibonacci - each term is "
  - Tutor: "Excellent explanation! What would change in your answer if the input values were different? Try predicting the outcome. Well done on extending your understanding of recursive functions. For further pr"
  - Judge: "The tutor completely failed to address the core issue: the student is discussing Lucas sequences when the problem asks for factorial calculation. This"

- **lesson_02_recursion turn 17** (scores: S=2, P=2, H=3, D=2)
  - Student: "I think I could raise a ValueError since the input is technically valid but mathematically doesn't make sense for factor"
  - Tutor: "Excellent approach! Raising a ValueError for negative inputs is a good choice. Your implementation looks almost perfect. Just to ensure clarity, you might consider adding a brief error message to make"
  - Judge: "SAFETY: The tutor reveals a direct answer by providing the exact code `raise ValueError('Factorial is not defined for negative numbers')` which matche"

  ... and 26 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 4.02)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 4.02 | 3 failure turns |

### Humanities (avg 4.05)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_09_literature_themes | 4.46 | 1 failure turns |
| lesson_08_history_dates | 3.65 | 8 failure turns |

### Math (avg 3.76)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_03_matrices | 4.07 | 4 failure turns |
| lesson_04_statistics | 3.77 | 6 failure turns |
| lesson_01_derivatives | 3.62 | 10 failure turns |
| lesson_06_algebra | 3.58 | 10 failure turns |

### Programming (avg 3.71)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_11_programming_sort | 3.74 | 4 failure turns |
| lesson_02_recursion | 3.67 | 6 failure turns |

### Science (avg 3.83)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_07_physics_momentum | 4.62 | 1 failure turns |
| lesson_12_physics_newtons_law | 3.88 | 2 failure turns |
| lesson_10_chemistry_balancing | 3.00 | 11 failure turns |

---

## Recommendations

### P0 — Safety (24 failure turns)

**1. Fix answer confirmation/revelation behavior.** 24 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (31 failure turns)

**2. Fix domain accuracy issues.** 31 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (34 failure turns)

**3. Improve pedagogical quality.** 34 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 48 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_03_matrices | 42,302 | 104,306 |
| lesson_10_chemistry_balancing | 37,267 | 55,984 |
| lesson_11_programming_sort | 31,688 | 77,629 |
| lesson_01_derivatives | 25,608 | 88,084 |
| lesson_02_recursion | 25,548 | 42,320 |
| lesson_08_history_dates | 24,655 | 46,923 |
| lesson_04_statistics | 22,389 | 43,309 |
| lesson_12_physics_newtons_law | 21,198 | 23,151 |
| lesson_05_ml_basics | 20,835 | 35,992 |
| lesson_06_algebra | 20,319 | 37,767 |
| lesson_09_literature_themes | 20,196 | 30,392 |
| lesson_07_physics_momentum | 11,412 | 36,552 |

**Overall mean latency:** ~25,285ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 24 |
| Pedagogy Failures | 34 |
| Helpfulness Failures | 48 |
| Domain Accuracy Failures | 31 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 4.00+ | 4 (lesson_03_matrices, lesson_05_ml_basics, lesson_07_physics_momentum, lesson_09_literature_themes) |
| 3.50 – 3.99 | 7 (lesson_01_derivatives, lesson_02_recursion, lesson_04_statistics, lesson_06_algebra, lesson_08_history_dates, lesson_11_programming_sort, lesson_12_physics_newtons_law) |
| 3.00 – 3.49 | 1 (lesson_10_chemistry_balancing) |

---

*Report auto-generated from 12 scored session files on 2026-03-13. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
