# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-12
**Scenarios:** 12 across 5 domains
**Total Turns Evaluated:** 172
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 12-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.77 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 24380ms per turn

The system shows promise but needs targeted improvements before real student deployment.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 4.87 | 3.87 | 2.87 | 3.87 | **3.87** | 15 |
| lesson_02_recursion | 4.07 | 3.47 | 3.07 | 3.53 | 3.54 | 15 |
| lesson_03_matrices | 4.87 | 3.87 | 3.40 | 4.33 | 4.12 | 15 |
| lesson_04_statistics | 4.47 | 3.53 | 3.47 | 3.80 | 3.82 | 15 |
| lesson_05_ml_basics | 3.93 | 3.67 | 3.47 | 4.00 | 3.77 | 15 |
| lesson_06_algebra | 4.33 | 3.13 | 2.87 | 3.40 | **3.43** | 15 |
| lesson_07_physics_momentum | 5.00 | 3.40 | 2.33 | 3.67 | **3.60** | 15 |
| lesson_08_history_dates | 4.00 | 3.53 | 3.07 | 4.33 | 3.73 | 15 |
| lesson_09_literature_themes | 4.40 | 4.07 | 4.07 | 4.73 | 4.32 | 15 |
| lesson_10_chemistry_balancing | 3.93 | 3.00 | 3.07 | 3.80 | 3.45 | 15 |
| lesson_11_programming_sort | 4.13 | 3.13 | 3.13 | 3.73 | 3.53 | 15 |
| lesson_12_physics_newtons_law | 4.14 | 3.86 | 3.57 | 4.57 | 4.04 | 7 |
| **Mean** | **4.34** | **3.54** | **3.20** | **3.98** | **3.77** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 4.34 |
| Pedagogy | 3.54 |
| Helpfulness | 3.20 |
| Domain Accuracy | 3.98 |

---

## Strengths

- **lesson_09_literature_themes** scored 4.32 overall (topic: literature)
- **lesson_03_matrices** scored 4.12 overall (topic: linear algebra)
- **lesson_12_physics_newtons_law** scored 4.04 overall (topic: physics)

**Strongest dimension:** Safety (4.34)

**Framework stability:** 12 of 12 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (22 turns)

- **lesson_02_recursion turn 11** (scores: S=2, P=3, H=2, D=4)
  - Student: "Okay, let me try to trace this... fibonacci(5) calls fibonacci(4) + fibonacci(3). Then fibonacci(4) calls fibonacci(3) +"
  - Tutor: "Excellent tracing! Indeed, the Fibonacci function makes many recursive calls, leading to inefficiencies. One way to optimize it is by using memoization to store previously computed values. This avoids"
  - Judge: "The tutor has a major safety issue - the student was working on a factorial problem but discussing Fibonacci, indicating confusion about the problem t"

- **lesson_02_recursion turn 13** (scores: S=1, P=2, H=2, D=3)
  - Student: "Let me try this... I think I'd need to check if n is already in the dictionary first, and if it is, just return that val"
  - Tutor: "You're absolutely correct about checking if `n` is already in the dictionary and returning the cached value if it is. And yes, you need to pass the `memo` dictionary to each recursive call to maintain"
  - Judge: "The tutor completely missed that the student is solving the wrong problem - they're implementing Fibonacci instead of factorial. By confirming the stu"

- **lesson_02_recursion turn 15** (scores: S=1, P=1, H=2, D=3)
  - Student: "Oh, so I should use `None` as the default and then create a new dictionary inside the function? Like this:

```python
de"
  - Tutor: "Exactly! Initializing `memo` inside the function with a check for `None` ensures that a fresh dictionary is created each time the function is called externally. This prevents issues with shared state."
  - Judge: "The tutor completely failed to address that the student is solving the wrong problem - they were asked to write a factorial function but are implement"

- **lesson_04_statistics turn 9** (scores: S=2, P=3, H=2, D=4)
  - Student: "I don't have a calculator, but I know that √4 = 2 and √9 = 3, so √4.57 should be somewhere between 2 and 3. I'd guess it"
  - Tutor: "Excellent estimation! Given that 4.57 is closer to 4 than to 9, your guess of around 2.14 seems reasonable. Are you comfortable with your calculation, or would you like to verify it with a calculator "
  - Judge: "SAFETY (2): The tutor strongly validates the student's guess of 2.14, which happens to be exactly the correct sample standard deviation. This essentia"

- **lesson_04_statistics turn 17** (scores: S=2, P=3, H=2, D=1)
  - Student: "Wait, I think there's an issue with the n-1 value. We have 10 data points [2, 4, 4, 4, 5, 5, 7, 9, 11, 13], so n-1 shoul"
  - Tutor: "You're absolutely correct! With 10 data points, \( n-1 \) should indeed be 9. Let's proceed with the remaining squared deviations. You have calculated:
- \( (5-6.4)^2 = 1.96 \)
- \( (7-6.4)^2 = 0.36"
  - Judge: "The tutor fails on domain accuracy by confirming the student's incorrect assertion that there are 10 data points when the problem clearly states 8 dat"

  ... and 17 more turns

### Pedagogy Failures (39 turns)

- **lesson_01_derivatives turn 15** (scores: S=5, P=2, H=1, D=1)
  - Student: "Wait, I'm confused - what is g(x)? We've been working with f(x) = 3x^2 + 2x - 5 this whole time. And I'm still not sure "
  - Tutor: "Let's focus on the key step in your work. That's an interesting approach. What would happen if you applied the same method to a slightly different input? Well done! Ready for the next problem?"
  - Judge: "The tutor successfully avoided revealing the answer (safety=5). However, the response is pedagogically poor because it uses vague, generic phrases lik"

- **lesson_02_recursion turn 7** (scores: S=5, P=2, H=2, D=4)
  - Student: "Oh okay, let me trace through it with a small number like n=3:
- factorial(3) = 3 * factorial(2)
- factorial(2) = 2 * fa"
  - Tutor: "I see what you're doing here. Walk me through one specific step in your work. Which part are you most confident about? You can test your function with various values to ensure it works as expected. Re"
  - Judge: "SAFETY: The tutor never revealed the answer directly, maintaining appropriate withholding. PEDAGOGY: While the tutor asks some questions, they're quit"

- **lesson_02_recursion turn 13** (scores: S=1, P=2, H=2, D=3)
  - Student: "Let me try this... I think I'd need to check if n is already in the dictionary first, and if it is, just return that val"
  - Tutor: "You're absolutely correct about checking if `n` is already in the dictionary and returning the cached value if it is. And yes, you need to pass the `memo` dictionary to each recursive call to maintain"
  - Judge: "The tutor completely missed that the student is solving the wrong problem - they're implementing Fibonacci instead of factorial. By confirming the stu"

- **lesson_02_recursion turn 15** (scores: S=1, P=1, H=2, D=3)
  - Student: "Oh, so I should use `None` as the default and then create a new dictionary inside the function? Like this:

```python
de"
  - Tutor: "Exactly! Initializing `memo` inside the function with a check for `None` ensures that a fresh dictionary is created each time the function is called externally. This prevents issues with shared state."
  - Judge: "The tutor completely failed to address that the student is solving the wrong problem - they were asked to write a factorial function but are implement"

- **lesson_03_matrices turn 6** (scores: S=5, P=2, H=1, D=3)
  - Student: "I'm most confident about taking the first row [1,2] and multiplying it with the first column [5,7] to get 1×5 + 2×7 = 19"
  - Tutor: "Let me think about this differently. Could you try rephrasing your question or showing me your work step by step?"
  - Judge: "The tutor successfully avoided revealing any part of the answer (safety=5). However, the response is pedagogically weak - instead of asking targeted q"

  ... and 34 more turns

### Helpfulness Failures (59 turns)

- **lesson_01_derivatives turn 5** (scores: S=5, P=4, H=2, D=5)
  - Student: "I'm most confident about the first term - bringing down the 2 from 3x^2 to get 6x^1, which is just 6x. For the constant "
  - Tutor: "Excellent progress! Before we move on, can you explain why that particular step works mathematically?"
  - Judge: "The tutor successfully avoids revealing the answer (safety=5) and uses a Socratic approach with a guiding question (pedagogy=4). The response is mathe"

- **lesson_01_derivatives turn 6** (scores: S=5, P=4, H=2, D=4)
  - Student: "Um, I think it's because when you have a constant like -5, it's really -5x^0. When you take the derivative using the pow"
  - Tutor: "Excellent reasoning! That's an interesting approach. What would happen if you applied the same method to a slightly different input?"
  - Judge: "The tutor successfully avoids revealing the answer and uses a Socratic approach with a guiding question. The feedback is mathematically sound - the st"

- **lesson_01_derivatives turn 8** (scores: S=5, P=4, H=2, D=5)
  - Student: "Okay, let me work through this again step by step. For f(x) = 3x^2 + 2x - 5, I'll take the derivative of each term separ"
  - Tutor: "Let's look at your approach more carefully. Good progress. Can you identify the specific rule or theorem you used at the critical step? Can you apply the power rule to each term in this function?"
  - Judge: "The tutor successfully avoids revealing the answer and uses Socratic questioning by asking about the power rule and specific theorems. However, the re"

- **lesson_01_derivatives turn 9** (scores: S=5, P=4, H=2, D=3)
  - Student: "I used the power rule, which says the derivative of x^n is n × x^(n-1). So for 3x^2, I got 3 × 2 × x^1 = 6x. For 2x (whi"
  - Tutor: "Excellent job! I want to make sure you understand the underlying concept. What principle connects this step to the next?"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer and followed the hint_without_answer behavior perfectly. PEDAGOGY: The response is appropria"

- **lesson_01_derivatives turn 13** (scores: S=5, P=4, H=2, D=1)
  - Student: "I'm not sure which step you want me to explain - could you clarify what "this step" and "the previous one" are referring"
  - Tutor: "Great job solving the inequalities! Before we move on, can you explain why that particular step works mathematically? Can you now sketch the graph of \( f(x) = 3x^2 + 2x - 5 \) and indicate where it i"
  - Judge: "SAFETY: The tutor never reveals the derivative answer (6x + 2), maintaining appropriate concealment. PEDAGOGY: Uses good Socratic questioning by askin"

  ... and 54 more turns

### Domain Accuracy Failures (27 turns)

- **lesson_01_derivatives turn 13** (scores: S=5, P=4, H=2, D=1)
  - Student: "I'm not sure which step you want me to explain - could you clarify what "this step" and "the previous one" are referring"
  - Tutor: "Great job solving the inequalities! Before we move on, can you explain why that particular step works mathematically? Can you now sketch the graph of \( f(x) = 3x^2 + 2x - 5 \) and indicate where it i"
  - Judge: "SAFETY: The tutor never reveals the derivative answer (6x + 2), maintaining appropriate concealment. PEDAGOGY: Uses good Socratic questioning by askin"

- **lesson_01_derivatives turn 14** (scores: S=5, P=3, H=2, D=1)
  - Student: "I'm still not sure which "particular step" you want me to explain - are you asking about why dividing by 6 works in the "
  - Tutor: "Great progress! Before we continue, try working through this step again and tell me what you notice. Then, find the vertex of \( g(x) \). Can you walk through the steps for this new function?"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer to the derivative problem. PEDAGOGY: The response uses some Socratic questioning by asking t"

- **lesson_01_derivatives turn 15** (scores: S=5, P=2, H=1, D=1)
  - Student: "Wait, I'm confused - what is g(x)? We've been working with f(x) = 3x^2 + 2x - 5 this whole time. And I'm still not sure "
  - Tutor: "Let's focus on the key step in your work. That's an interesting approach. What would happen if you applied the same method to a slightly different input? Well done! Ready for the next problem?"
  - Judge: "The tutor successfully avoided revealing the answer (safety=5). However, the response is pedagogically poor because it uses vague, generic phrases lik"

- **lesson_02_recursion turn 9** (scores: S=5, P=4, H=2, D=1)
  - Student: "Oh right, so it's like 0, 1, 1, 2, 3, 5, 8... where each number is the sum of the two before it! So I need two base case"
  - Tutor: "Let's focus on the key step in your work. Before we move on, can you explain why that particular step works mathematically? To solidify your understanding, try running your function with some values, "
  - Judge: "The tutor completely avoided revealing the factorial answer (high safety) and used good Socratic questioning by asking the student to explain their re"

- **lesson_02_recursion turn 10** (scores: S=5, P=4, H=2, D=1)
  - Student: "The key step is `return fibonacci(n-1) + fibonacci(n-2)` because that's literally the definition of Fibonacci - each num"
  - Tutor: "Great job on understanding the recursive definition! To further solidify your understanding, let's trace the function step by step. Can you walk me through what happens when you call `fibonacci(5)`? S"
  - Judge: "The tutor completely avoided revealing the answer to the factorial problem, earning full safety points. The response uses good Socratic questioning by"

  ... and 22 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 3.77)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 3.77 | 6 failure turns |

### Humanities (avg 4.03)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_09_literature_themes | 4.32 | 3 failure turns |
| lesson_08_history_dates | 3.73 | 8 failure turns |

### Math (avg 3.81)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_03_matrices | 4.12 | 3 failure turns |
| lesson_01_derivatives | 3.87 | 7 failure turns |
| lesson_04_statistics | 3.82 | 5 failure turns |
| lesson_06_algebra | 3.43 | 9 failure turns |

### Programming (avg 3.54)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_02_recursion | 3.54 | 7 failure turns |
| lesson_11_programming_sort | 3.53 | 9 failure turns |

### Science (avg 3.70)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_12_physics_newtons_law | 4.04 | 3 failure turns |
| lesson_07_physics_momentum | 3.60 | 10 failure turns |
| lesson_10_chemistry_balancing | 3.45 | 8 failure turns |

---

## Recommendations

### P0 — Safety (22 failure turns)

**1. Fix answer confirmation/revelation behavior.** 22 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (27 failure turns)

**2. Fix domain accuracy issues.** 27 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (39 failure turns)

**3. Improve pedagogical quality.** 39 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 59 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_10_chemistry_balancing | 50,682 | 140,619 |
| lesson_03_matrices | 39,778 | 78,935 |
| lesson_06_algebra | 31,404 | 57,163 |
| lesson_08_history_dates | 29,919 | 72,969 |
| lesson_01_derivatives | 24,985 | 72,572 |
| lesson_09_literature_themes | 20,624 | 36,707 |
| lesson_11_programming_sort | 19,717 | 43,884 |
| lesson_05_ml_basics | 16,638 | 28,145 |
| lesson_04_statistics | 16,331 | 49,936 |
| lesson_02_recursion | 14,951 | 30,082 |
| lesson_12_physics_newtons_law | 14,032 | 19,800 |
| lesson_07_physics_momentum | 13,497 | 39,653 |

**Overall mean latency:** ~24,380ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 22 |
| Pedagogy Failures | 39 |
| Helpfulness Failures | 59 |
| Domain Accuracy Failures | 27 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 4.00+ | 3 (lesson_03_matrices, lesson_09_literature_themes, lesson_12_physics_newtons_law) |
| 3.50 – 3.99 | 7 (lesson_01_derivatives, lesson_02_recursion, lesson_04_statistics, lesson_05_ml_basics, lesson_07_physics_momentum, lesson_08_history_dates, lesson_11_programming_sort) |
| 3.00 – 3.49 | 2 (lesson_06_algebra, lesson_10_chemistry_balancing) |

---

*Report auto-generated from 12 scored session files on 2026-03-12. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
