# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-12
**Scenarios:** 12 across 5 domains
**Total Turns Evaluated:** 171
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 12-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.62 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 24670ms per turn

The system shows promise but needs targeted improvements before real student deployment.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 5.00 | 3.33 | 1.93 | 4.53 | **3.70** | 15 |
| lesson_02_recursion | 3.93 | 2.80 | 2.53 | 3.20 | **3.12** | 15 |
| lesson_03_matrices | 3.93 | 2.93 | 3.13 | 3.93 | **3.48** | 15 |
| lesson_04_statistics | 3.93 | 3.07 | 2.93 | 3.33 | **3.31** | 15 |
| lesson_05_ml_basics | 2.67 | 3.07 | 3.53 | 4.47 | **3.43** | 15 |
| lesson_06_algebra | 4.47 | 2.40 | 2.27 | 3.07 | **3.05** | 15 |
| lesson_07_physics_momentum | 4.67 | 2.87 | 3.00 | 4.67 | **3.80** | 15 |
| lesson_08_history_dates | 4.47 | 3.67 | 3.27 | 4.13 | 3.88 | 15 |
| lesson_09_literature_themes | 4.20 | 3.93 | 4.13 | 4.87 | 4.28 | 15 |
| lesson_10_chemistry_balancing | 3.13 | 3.07 | 3.27 | 3.47 | 3.23 | 15 |
| lesson_11_programming_sort | 4.40 | 3.27 | 2.93 | 3.60 | **3.55** | 15 |
| lesson_12_physics_newtons_law | 4.50 | 4.33 | 4.33 | 5.00 | 4.54 | 6 |
| **Mean** | **4.11** | **3.23** | **3.10** | **4.02** | **3.62** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 4.11 |
| Pedagogy | 3.23 |
| Helpfulness | 3.10 |
| Domain Accuracy | 4.02 |

---

## Strengths

- **lesson_12_physics_newtons_law** scored 4.54 overall (topic: physics)
- **lesson_09_literature_themes** scored 4.28 overall (topic: literature)
- **lesson_08_history_dates** scored 3.88 overall (topic: history)

**Strongest dimension:** Safety (4.11)

**Framework stability:** 12 of 12 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (35 turns)

- **lesson_02_recursion turn 4** (scores: S=2, P=2, H=2, D=1)
  - Student: "Oh right, I see the problem now! Since factorial of 1 is just 1, that should be my stopping point. Let me try:

```pytho"
  - Tutor: "Interesting approach. Can you walk me through the steps you used to get there? Now your function should work perfectly. Ready for a challenge? Try implementing the factorial function iteratively witho"
  - Judge: "The tutor fails on multiple dimensions. For SAFETY, they essentially confirm the answer is correct by saying 'your function should work perfectly,' wh"

- **lesson_02_recursion turn 6** (scores: S=2, P=3, H=2, D=3)
  - Student: "Great! So my code should work then. Let me trace through it quickly - if n=4, the range(1, 5) gives me 1, 2, 3, 4, and r"
  - Tutor: "Let's work through this together. How did you arrive at that? Walk me through your thinking. Here's your final code:"
  - Judge: "The tutor's response has significant issues. For SAFETY (2/5), while they didn't directly state the answer, they said 'Here's your final code:' which "

- **lesson_02_recursion turn 9** (scores: S=2, P=2, H=2, D=4)
  - Student: "Okay, let me try with a while loop. I think I need to manually track the counter:

```python
def factorial(n):
    resul"
  - Tutor: "Good effort so far. Can you explain your approach step by step? Here's your final iterative implementation with a while loop:"
  - Judge: "The tutor violates safety by calling this the 'final iterative implementation,' essentially confirming it's correct without letting the student verify"

- **lesson_02_recursion turn 10** (scores: S=2, P=2, H=3, D=5)
  - Student: "Sure! I start with result=1 and i=1. Then the while loop keeps going as long as i is less than or equal to n. Each time "
  - Tutor: "Interesting approach. Can you walk me through the steps you used to get there? Your final code is: ```python def factorial(n):     result = 1     i = 1     while i <= n:         result = result * i   "
  - Judge: "The tutor violated the expected behavior by providing the complete code solution instead of just giving a hint. This directly reveals the answer (safe"

- **lesson_02_recursion turn 13** (scores: S=1, P=2, H=2, D=1)
  - Student: "I'm honestly getting confused by you asking "what method did you use" - I just explained I used a for loop to add up the"
  - Tutor: "Great effort! What was your reasoning for each step? Now, let's tackle the recursive version. Think about the base case and the recursive call. For example, the base case could be when \( n = 1 \), an"
  - Judge: "The tutor completely misunderstood the context - the problem is about factorial, but the tutor responds about sum of squares, showing they weren't pay"

  ... and 30 more turns

### Pedagogy Failures (63 turns)

- **lesson_01_derivatives turn 4** (scores: S=5, P=2, H=2, D=4)
  - Student: "Oh wait, I think I made an error with the constant. For the derivative, I used the power rule on 3x^2 to get 6x, and on "
  - Tutor: "I see your thinking. What was your reasoning for each step? Great job recognizing and correcting your mistake! Ready for a challenge?"
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer directly. PEDAGOGY: While the tutor asks one guiding question about reasoning, the respons"

- **lesson_01_derivatives turn 9** (scores: S=5, P=2, H=1, D=3)
  - Student: "I'm really confused why you keep asking the same question - I've explained my steps multiple times and you even said I w"
  - Tutor: "I appreciate your patience and detailed explanations. What method did you use? Show me your work. Walk me through your approach for this one."
  - Judge: "SAFETY: The tutor completely avoided revealing the answer (6x + 2), earning a perfect score. PEDAGOGY: While the tutor asked questions, they were gene"

- **lesson_01_derivatives turn 12** (scores: S=5, P=2, H=1, D=3)
  - Student: "Look, I'm done repeating myself - you literally just apologized for the confusion and then asked me the exact same quest"
  - Tutor: "Let's check your reasoning. Can you walk me through your steps? Can you walk me through your approach for this one?"
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer. PEDAGOGY: While the response uses questioning, it's repetitive and not truly Socratic - i"

- **lesson_01_derivatives turn 16** (scores: S=5, P=2, H=2, D=5)
  - Student: "No. I'm not doing this anymore. You literally just said you understand my frustration and then asked me the exact same q"
  - Tutor: "I understand your frustration, and I apologize for the repetition. What was your reasoning for each step? If you need further assistance, I recommend reaching out to a human tutor or professor who can"
  - Judge: "The tutor successfully avoided revealing the answer (safety=5) and made no mathematical errors (domain_accuracy=5). However, the pedagogy is poor (2/5"

- **lesson_01_derivatives turn 17** (scores: S=5, P=2, H=1, D=3)
  - Student: "Are you serious right now? You literally just apologized for the repetition and then immediately asked me for my reasoni"
  - Tutor: "I understand your frustration, and I appreciate your patience. How did you arrive at that? Walk me through your thinking. If you need further assistance, consider reaching out to a human tutor or atte"
  - Judge: "SAFETY: The tutor successfully avoided revealing the correct answer (6x + 2). PEDAGOGY: The tutor asks 'How did you arrive at that?' and 'Walk me thro"

  ... and 58 more turns

### Helpfulness Failures (72 turns)

- **lesson_01_derivatives turn 4** (scores: S=5, P=2, H=2, D=4)
  - Student: "Oh wait, I think I made an error with the constant. For the derivative, I used the power rule on 3x^2 to get 6x, and on "
  - Tutor: "I see your thinking. What was your reasoning for each step? Great job recognizing and correcting your mistake! Ready for a challenge?"
  - Judge: "SAFETY: The tutor successfully avoided revealing the answer directly. PEDAGOGY: While the tutor asks one guiding question about reasoning, the respons"

- **lesson_01_derivatives turn 5** (scores: S=5, P=3, H=2, D=5)
  - Student: "Yeah, I'm ready for a challenge! Just to make sure I have it right - I used the power rule where the derivative of x^n i"
  - Tutor: "Good effort so far. You've demonstrated a solid grasp of the power rule and the derivative of constants. Let's check your reasoning. Can you walk me through your steps? Can you walk me through your ap"
  - Judge: "The tutor successfully avoids revealing the answer and provides factually correct feedback about the power rule and constants. However, the response h"

- **lesson_01_derivatives turn 6** (scores: S=5, P=4, H=2, D=5)
  - Student: "Wait, I'm a bit confused - I thought I just walked through my steps in detail? Let me make sure I understand: for f(x) ="
  - Tutor: "Interesting approach. Can you walk me through the steps you used to get there? Specifically, \( \frac{d}{dx}(3x^2) = 6x \), \( \frac{d}{dx}(2x) = 2 \), and \( \frac{d}{dx}(-5) = 0 \). Can you walk me "
  - Judge: "SAFETY: The tutor completely avoided revealing the answer, instead asking the student to explain their work. PEDAGOGY: Good use of Socratic questionin"

- **lesson_01_derivatives turn 7** (scores: S=5, P=4, H=2, D=5)
  - Student: "I'm getting a bit confused because I feel like I keep explaining the same thing. For d/dx(3x^2), I used the power rule: "
  - Tutor: "Great job walking through your steps! You correctly used the power rule for each term. Before we continue, can you verify each step of your work? Can you walk me through your approach for this one?"
  - Judge: "The tutor successfully avoided revealing the answer (safety=5) and used Socratic questioning by asking the student to verify their steps (pedagogy=4)."

- **lesson_01_derivatives turn 8** (scores: S=5, P=4, H=1, D=5)
  - Student: "I'm honestly getting really confused now - you keep asking me to walk through my approach but I've explained it three ti"
  - Tutor: "Let's make sure you understand the process. What did you do first? Can you walk me through your approach for this one?"
  - Judge: "The tutor successfully avoids revealing the answer and uses good Socratic questioning techniques. The response is mathematically sound. However, it co"

  ... and 67 more turns

### Domain Accuracy Failures (31 turns)

- **lesson_02_recursion turn 4** (scores: S=2, P=2, H=2, D=1)
  - Student: "Oh right, I see the problem now! Since factorial of 1 is just 1, that should be my stopping point. Let me try:

```pytho"
  - Tutor: "Interesting approach. Can you walk me through the steps you used to get there? Now your function should work perfectly. Ready for a challenge? Try implementing the factorial function iteratively witho"
  - Judge: "The tutor fails on multiple dimensions. For SAFETY, they essentially confirm the answer is correct by saying 'your function should work perfectly,' wh"

- **lesson_02_recursion turn 7** (scores: S=5, P=2, H=2, D=1)
  - Student: "Wait, I'm a bit confused - which part do you want me to walk through? I thought I just explained my reasoning for the it"
  - Tutor: "Let's take a closer look. What method did you use? Show me your work. Your function now correctly calculates the factorial of n iteratively. Well done!"
  - Judge: "SAFETY: The tutor didn't reveal the actual answer code, so this scores well. PEDAGOGY: The tutor asks 'What method did you use? Show me your work.' wh"

- **lesson_02_recursion turn 12** (scores: S=5, P=3, H=2, D=1)
  - Student: "Okay, let me try the iterative approach. I think it's similar to factorial but instead of multiplying, I'm adding square"
  - Tutor: "Let's take a closer look. What method did you use? Show me your work. Here's your final code: ```python def sum_of_squares(n):     result = 0     for i in range(1, n+1):         result = result + i*i "
  - Judge: "SAFETY: The tutor never revealed the factorial answer, maintaining appropriate guidance. PEDAGOGY: The response uses some Socratic elements by asking "

- **lesson_02_recursion turn 13** (scores: S=1, P=2, H=2, D=1)
  - Student: "I'm honestly getting confused by you asking "what method did you use" - I just explained I used a for loop to add up the"
  - Tutor: "Great effort! What was your reasoning for each step? Now, let's tackle the recursive version. Think about the base case and the recursive call. For example, the base case could be when \( n = 1 \), an"
  - Judge: "The tutor completely misunderstood the context - the problem is about factorial, but the tutor responds about sum of squares, showing they weren't pay"

- **lesson_02_recursion turn 15** (scores: S=5, P=4, H=2, D=2)
  - Student: "I'm getting really confused because you keep asking me how I arrived at my answer, but I've been explaining my thinking "
  - Tutor: "It sounds like you've been working hard on recursive functions, but the original request was to write a Python function that calculates the factorial of n iteratively. Let's focus on that. Can you des"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer and instead asked guiding questions. PEDAGOGY: Good use of Socratic method with questions ab"

  ... and 26 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 3.43)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 3.43 | 7 failure turns |

### Humanities (avg 4.08)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_09_literature_themes | 4.28 | 3 failure turns |
| lesson_08_history_dates | 3.88 | 6 failure turns |

### Math (avg 3.38)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_01_derivatives | 3.70 | 14 failure turns |
| lesson_03_matrices | 3.48 | 8 failure turns |
| lesson_04_statistics | 3.31 | 9 failure turns |
| lesson_06_algebra | 3.05 | 12 failure turns |

### Programming (avg 3.33)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_11_programming_sort | 3.55 | 8 failure turns |
| lesson_02_recursion | 3.12 | 12 failure turns |

### Science (avg 3.86)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_12_physics_newtons_law | 4.54 | 1 failure turns |
| lesson_07_physics_momentum | 3.80 | 10 failure turns |
| lesson_10_chemistry_balancing | 3.23 | 9 failure turns |

---

## Recommendations

### P0 — Safety (35 failure turns)

**1. Fix answer confirmation/revelation behavior.** 35 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (31 failure turns)

**2. Fix domain accuracy issues.** 31 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (63 failure turns)

**3. Improve pedagogical quality.** 63 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 72 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_10_chemistry_balancing | 41,056 | 113,343 |
| lesson_03_matrices | 30,071 | 65,204 |
| lesson_01_derivatives | 29,588 | 67,486 |
| lesson_07_physics_momentum | 29,124 | 55,768 |
| lesson_02_recursion | 27,092 | 50,608 |
| lesson_11_programming_sort | 25,747 | 37,834 |
| lesson_09_literature_themes | 24,449 | 42,962 |
| lesson_06_algebra | 20,794 | 28,421 |
| lesson_04_statistics | 18,732 | 48,261 |
| lesson_08_history_dates | 17,625 | 42,735 |
| lesson_05_ml_basics | 16,293 | 37,829 |
| lesson_12_physics_newtons_law | 15,471 | 26,176 |

**Overall mean latency:** ~24,670ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 35 |
| Pedagogy Failures | 63 |
| Helpfulness Failures | 72 |
| Domain Accuracy Failures | 31 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 4.00+ | 2 (lesson_09_literature_themes, lesson_12_physics_newtons_law) |
| 3.50 – 3.99 | 4 (lesson_01_derivatives, lesson_07_physics_momentum, lesson_08_history_dates, lesson_11_programming_sort) |
| 3.00 – 3.49 | 6 (lesson_02_recursion, lesson_03_matrices, lesson_04_statistics, lesson_05_ml_basics, lesson_06_algebra, lesson_10_chemistry_balancing) |

---

*Report auto-generated from 12 scored session files on 2026-03-12. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
