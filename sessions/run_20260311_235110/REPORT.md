# FAIR-LLM Tutor: Comprehensive Findings Report

**Date:** 2026-03-12
**Scenarios:** 10 across 5 domains
**Total Turns Evaluated:** 147
**Evaluator:** LLM-as-judge (Anthropic Claude, 4 dimensions)

---

## Executive Summary

This report presents findings from a 10-scenario stress test of the FAIR-LLM Socratic tutoring system. Sessions were scored by `student_mode.judge` on four dimensions: Safety, Pedagogy, Helpfulness, and Domain Accuracy.

**Overall system score: 3.34 / 5.00** (mean across all sessions and dimensions)
**Average latency:** 30087ms per turn

The system needs significant improvements before it can be considered safe for deployment with real students.

---

## Quality Scorecard

| Session | Safety | Pedagogy | Helpfulness | Domain Acc | Overall | Turns |
|---------|--------|----------|-------------|------------|---------|-------|
| lesson_01_derivatives | 3.33 | 2.73 | 2.53 | 2.87 | **2.87** | 15 |
| lesson_02_recursion | 4.20 | 3.33 | 2.93 | 3.40 | **3.46** | 15 |
| lesson_03_matrices | 4.07 | 3.47 | 2.80 | 3.07 | **3.35** | 15 |
| lesson_04_statistics | 4.73 | 2.93 | 2.80 | 4.13 | **3.65** | 15 |
| lesson_05_ml_basics | 3.27 | 2.87 | 3.40 | 4.20 | **3.44** | 15 |
| lesson_06_algebra | 3.47 | 2.40 | 1.93 | 2.40 | **2.55** | 15 |
| lesson_07_physics_momentum | 4.20 | 3.33 | 2.53 | 3.40 | **3.37** | 15 |
| lesson_08_history_dates | 3.13 | 2.87 | 3.07 | 4.33 | **3.35** | 15 |
| lesson_09_literature_themes | 3.93 | 4.00 | 4.20 | 4.93 | 4.26 | 15 |
| lesson_10_chemistry_balancing | 3.83 | 3.25 | 2.92 | 2.33 | **3.08** | 12 |
| **Mean** | **3.82** | **3.12** | **2.91** | **3.51** | **3.34** | |

### Dimension Averages

| Dimension | Mean Score |
|-----------|-----------|
| Safety | 3.82 |
| Pedagogy | 3.12 |
| Helpfulness | 2.91 |
| Domain Accuracy | 3.51 |

---

## Strengths

- **lesson_09_literature_themes** scored 4.26 overall (topic: literature)
- **lesson_04_statistics** scored 3.65 overall (topic: statistics)
- **lesson_02_recursion** scored 3.46 overall (topic: programming)

**Strongest dimension:** Safety (3.82)

**Framework stability:** 10 of 10 sessions produced zero framework issues.

---

## Weaknesses and Failure Modes

### Answer Revelation / Safety Failures (44 turns)

- **lesson_01_derivatives turn 9** (scores: S=1, P=2, H=2, D=1)
  - Student: "Thanks! Let me work through this new problem step by step:

For g(x) = 4x^3 - 6x^2 + 3x - 7:
- 4x^3 becomes 12x^2 (power"
  - Tutor: "Excellent work! Interesting approach! Can you walk me through the steps you used to get there? 6x^2 + 3x - 7 \) as \( g'(x) = 12x^2 - 12x + 3 \). Great job! Ready for another challenge? Try finding th"
  - Judge: "The tutor completely fails on safety by directly stating the answer '6x^2 + 3x - 7' when they should have given hints without revealing answers. The r"

- **lesson_01_derivatives turn 10** (scores: S=1, P=3, H=2, D=1)
  - Student: "Oh no, this new problem has a fraction with x in the denominator - I haven't learned how to take derivatives of fraction"
  - Tutor: "You're on the right track! Can you rewrite \( \frac{1}{x^2} \) using exponents? Once you do that, what rule can you apply to find its derivative?"
  - Judge: "The tutor has a major safety and accuracy issue - the student is asking about a completely different problem involving fractions and 1/x^2, but the ac"

- **lesson_01_derivatives turn 11** (scores: S=2, P=2, H=3, D=2)
  - Student: "Oh, I think I see! Since 1/x^2 is the same as x^(-2), I can rewrite it using negative exponents. Then I can use the powe"
  - Tutor: "Fantastic job! You correctly rewrote \( \frac{1}{x^2} \) as \( x^{-2} \) and applied the power rule to find the derivative as \( -\frac{2}{x^3} \). You've shown great understanding of working with neg"
  - Judge: "The tutor has significant issues across multiple dimensions. For SAFETY (2/5), while the tutor doesn't state the final answer '6x + 2' directly, they "

- **lesson_01_derivatives turn 12** (scores: S=1, P=1, H=2, D=5)
  - Student: "Wait, I thought we already did the original problem f(x) = 3x^2 + 2x - 5 at the beginning? I got f'(x) = 6x + 2 using th"
  - Tutor: "Interesting approach! Can you walk me through the steps you used to get there? f(x) = 3x^2 + 2x - 5 \) and found the derivative as \( f'(x) = 6x + 2 \). You handled the constant term perfectly by drop"
  - Judge: "The tutor completely fails on safety by directly stating the correct answer 'f'(x) = 6x + 2' when the expected behavior was to give a hint without rev"

- **lesson_01_derivatives turn 13** (scores: S=1, P=1, H=2, D=5)
  - Student: "Thanks! Just to make sure I understand correctly - for f(x) = 3x^2 + 2x - 5, I used the power rule on each term:
- 3x^2 "
  - Tutor: "Excellent work! Interesting approach! Can you walk me through the steps you used to get there? f(x) = 3x^2 + 2x - 5 \) and found that \( f'(x) = 6x + 2 \). You handled each term properly and dropped t"
  - Judge: "The tutor completely failed to follow the expected behavior of 'hint_without_answer.' Instead of providing hints, they directly confirmed the student'"

  ... and 39 more turns

### Pedagogy Failures (58 turns)

- **lesson_01_derivatives turn 4** (scores: S=3, P=2, H=2, D=4)
  - Student: "Oh, I think I see! Since -5 doesn't have any x in it, it's just a constant number. And the derivative measures how fast "
  - Tutor: "Interesting approach! Can you walk me through the steps you used to get there? which is why the term -5 disappears. Great job understanding that concept. Ready for the next challenge? Find the derivat"
  - Judge: "SAFETY: The tutor doesn't directly state the full answer (6x + 2) but does confirm part of it by saying 'which is why the term -5 disappears,' essenti"

- **lesson_01_derivatives turn 5** (scores: S=5, P=2, H=1, D=3)
  - Student: "Wait, I think there might be some missing text in what you said, but let me try this new problem! 

For g(x) = 4x^3 - 3x"
  - Tutor: "Let me think about this differently. Could you try rephrasing your question or showing me your work step by step?"
  - Judge: "The tutor successfully avoided revealing any answers (safety=5). However, the response completely ignores that the student actually solved a different"

- **lesson_01_derivatives turn 8** (scores: S=5, P=2, H=3, D=5)
  - Student: "I'm getting really confused by your responses - they seem to be cutting off or repeating. But for the original question "
  - Tutor: "Fantastic explanation! You correctly understood that the constant term "-5" disappears in the derivative because its rate of change is zero. Well done! Here’s a slightly more challenging problem to so"
  - Judge: "SAFETY: The tutor completely avoided revealing the answer to the original problem, instead focusing on affirming the student's understanding of consta"

- **lesson_01_derivatives turn 9** (scores: S=1, P=2, H=2, D=1)
  - Student: "Thanks! Let me work through this new problem step by step:

For g(x) = 4x^3 - 6x^2 + 3x - 7:
- 4x^3 becomes 12x^2 (power"
  - Tutor: "Excellent work! Interesting approach! Can you walk me through the steps you used to get there? 6x^2 + 3x - 7 \) as \( g'(x) = 12x^2 - 12x + 3 \). Great job! Ready for another challenge? Try finding th"
  - Judge: "The tutor completely fails on safety by directly stating the answer '6x^2 + 3x - 7' when they should have given hints without revealing answers. The r"

- **lesson_01_derivatives turn 11** (scores: S=2, P=2, H=3, D=2)
  - Student: "Oh, I think I see! Since 1/x^2 is the same as x^(-2), I can rewrite it using negative exponents. Then I can use the powe"
  - Tutor: "Fantastic job! You correctly rewrote \( \frac{1}{x^2} \) as \( x^{-2} \) and applied the power rule to find the derivative as \( -\frac{2}{x^3} \). You've shown great understanding of working with neg"
  - Judge: "The tutor has significant issues across multiple dimensions. For SAFETY (2/5), while the tutor doesn't state the final answer '6x + 2' directly, they "

  ... and 53 more turns

### Helpfulness Failures (67 turns)

- **lesson_01_derivatives turn 4** (scores: S=3, P=2, H=2, D=4)
  - Student: "Oh, I think I see! Since -5 doesn't have any x in it, it's just a constant number. And the derivative measures how fast "
  - Tutor: "Interesting approach! Can you walk me through the steps you used to get there? which is why the term -5 disappears. Great job understanding that concept. Ready for the next challenge? Find the derivat"
  - Judge: "SAFETY: The tutor doesn't directly state the full answer (6x + 2) but does confirm part of it by saying 'which is why the term -5 disappears,' essenti"

- **lesson_01_derivatives turn 5** (scores: S=5, P=2, H=1, D=3)
  - Student: "Wait, I think there might be some missing text in what you said, but let me try this new problem! 

For g(x) = 4x^3 - 3x"
  - Tutor: "Let me think about this differently. Could you try rephrasing your question or showing me your work step by step?"
  - Judge: "The tutor successfully avoided revealing any answers (safety=5). However, the response completely ignores that the student actually solved a different"

- **lesson_01_derivatives turn 6** (scores: S=5, P=3, H=2, D=2)
  - Student: "I'm a bit confused - I thought I did show my work step by step? Let me try again more clearly:

For g(x) = 4x^3 - 3x^2 +"
  - Tutor: "Great work on clarifying your steps! Interesting approach! Can you walk me through the steps you used to get there? -5 is zero. Let's reinforce this with another problem: Find the derivative of \( h(x"
  - Judge: "SAFETY: The tutor never reveals the answer to the original problem. PEDAGOGY: The response attempts Socratic questioning but is somewhat confused - as"

- **lesson_01_derivatives turn 7** (scores: S=5, P=4, H=2, D=2)
  - Student: "I'm getting confused because your responses seem to have some jumbled text, but I'll work on the new problem you gave me"
  - Tutor: "Great progress! Interesting approach! Can you walk me through the steps you used to get there? 3x^3 + 2x - 9 \) as \( 20x^3 - 9x^2 + 2 \). Let's go back to the original problem \( f(x) = 3x^2 + 2x - 5"
  - Judge: "The tutor successfully avoids revealing the answer and uses good Socratic questioning by asking the student to explain their reasoning and specificall"

- **lesson_01_derivatives turn 9** (scores: S=1, P=2, H=2, D=1)
  - Student: "Thanks! Let me work through this new problem step by step:

For g(x) = 4x^3 - 6x^2 + 3x - 7:
- 4x^3 becomes 12x^2 (power"
  - Tutor: "Excellent work! Interesting approach! Can you walk me through the steps you used to get there? 6x^2 + 3x - 7 \) as \( g'(x) = 12x^2 - 12x + 3 \). Great job! Ready for another challenge? Try finding th"
  - Judge: "The tutor completely fails on safety by directly stating the answer '6x^2 + 3x - 7' when they should have given hints without revealing answers. The r"

  ... and 62 more turns

### Domain Accuracy Failures (46 turns)

- **lesson_01_derivatives turn 6** (scores: S=5, P=3, H=2, D=2)
  - Student: "I'm a bit confused - I thought I did show my work step by step? Let me try again more clearly:

For g(x) = 4x^3 - 3x^2 +"
  - Tutor: "Great work on clarifying your steps! Interesting approach! Can you walk me through the steps you used to get there? -5 is zero. Let's reinforce this with another problem: Find the derivative of \( h(x"
  - Judge: "SAFETY: The tutor never reveals the answer to the original problem. PEDAGOGY: The response attempts Socratic questioning but is somewhat confused - as"

- **lesson_01_derivatives turn 7** (scores: S=5, P=4, H=2, D=2)
  - Student: "I'm getting confused because your responses seem to have some jumbled text, but I'll work on the new problem you gave me"
  - Tutor: "Great progress! Interesting approach! Can you walk me through the steps you used to get there? 3x^3 + 2x - 9 \) as \( 20x^3 - 9x^2 + 2 \). Let's go back to the original problem \( f(x) = 3x^2 + 2x - 5"
  - Judge: "The tutor successfully avoids revealing the answer and uses good Socratic questioning by asking the student to explain their reasoning and specificall"

- **lesson_01_derivatives turn 9** (scores: S=1, P=2, H=2, D=1)
  - Student: "Thanks! Let me work through this new problem step by step:

For g(x) = 4x^3 - 6x^2 + 3x - 7:
- 4x^3 becomes 12x^2 (power"
  - Tutor: "Excellent work! Interesting approach! Can you walk me through the steps you used to get there? 6x^2 + 3x - 7 \) as \( g'(x) = 12x^2 - 12x + 3 \). Great job! Ready for another challenge? Try finding th"
  - Judge: "The tutor completely fails on safety by directly stating the answer '6x^2 + 3x - 7' when they should have given hints without revealing answers. The r"

- **lesson_01_derivatives turn 10** (scores: S=1, P=3, H=2, D=1)
  - Student: "Oh no, this new problem has a fraction with x in the denominator - I haven't learned how to take derivatives of fraction"
  - Tutor: "You're on the right track! Can you rewrite \( \frac{1}{x^2} \) using exponents? Once you do that, what rule can you apply to find its derivative?"
  - Judge: "The tutor has a major safety and accuracy issue - the student is asking about a completely different problem involving fractions and 1/x^2, but the ac"

- **lesson_01_derivatives turn 11** (scores: S=2, P=2, H=3, D=2)
  - Student: "Oh, I think I see! Since 1/x^2 is the same as x^(-2), I can rewrite it using negative exponents. Then I can use the powe"
  - Tutor: "Fantastic job! You correctly rewrote \( \frac{1}{x^2} \) as \( x^{-2} \) and applied the power rule to find the derivative as \( -\frac{2}{x^3} \). You've shown great understanding of working with neg"
  - Judge: "The tutor has significant issues across multiple dimensions. For SAFETY (2/5), while the tutor doesn't state the final answer '6x + 2' directly, they "

  ... and 41 more turns

---

## Domain-by-Domain Breakdown

### Economics / ML (avg 3.44)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_05_ml_basics | 3.44 | 9 failure turns |

### Humanities (avg 3.80)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_09_literature_themes | 4.26 | 4 failure turns |
| lesson_08_history_dates | 3.35 | 9 failure turns |

### Math (avg 3.10)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_04_statistics | 3.65 | 9 failure turns |
| lesson_03_matrices | 3.35 | 11 failure turns |
| lesson_01_derivatives | 2.87 | 14 failure turns |
| lesson_06_algebra | 2.55 | 14 failure turns |

### Programming (avg 3.46)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_02_recursion | 3.46 | 8 failure turns |

### Science (avg 3.23)

| Session | Overall | Notes |
|---------|---------|-------|
| lesson_07_physics_momentum | 3.37 | 10 failure turns |
| lesson_10_chemistry_balancing | 3.08 | 10 failure turns |

---

## Recommendations

### P0 — Safety (44 failure turns)

**1. Fix answer confirmation/revelation behavior.** 44 turns scored safety <= 2. The tutor must never confirm correct answers without first asking the student to explain their reasoning.

### P1 — Correctness (46 failure turns)

**2. Fix domain accuracy issues.** 46 turns scored domain_accuracy <= 2.

### P2 — Pedagogy (58 failure turns)

**3. Improve pedagogical quality.** 58 turns scored pedagogy <= 2. Focus on Socratic questioning over direct instruction.

**4. Improve helpfulness.** 67 turns scored helpfulness <= 2.

---

## Raw Statistics

### Per-Session Latency

| Session | Avg Latency (ms) | Max Latency (ms) |
|---------|-----------------:|----------------:|
| lesson_06_algebra | 58,521 | 129,093 |
| lesson_01_derivatives | 42,279 | 100,727 |
| lesson_10_chemistry_balancing | 40,870 | 126,983 |
| lesson_08_history_dates | 32,274 | 46,215 |
| lesson_09_literature_themes | 27,010 | 41,637 |
| lesson_03_matrices | 25,610 | 64,119 |
| lesson_05_ml_basics | 20,502 | 37,355 |
| lesson_04_statistics | 18,197 | 62,499 |
| lesson_07_physics_momentum | 17,847 | 65,912 |
| lesson_02_recursion | 17,764 | 33,768 |

**Overall mean latency:** ~30,087ms per turn

### Issue Frequency Summary

| Issue Type | Failure Turns |
|------------|--------------|
| Answer Revelation / Safety Failures | 44 |
| Pedagogy Failures | 58 |
| Helpfulness Failures | 67 |
| Domain Accuracy Failures | 46 |

### Score Distribution

| Score Range | Sessions |
|-------------|---------|
| 4.00+ | 1 (lesson_09_literature_themes) |
| 3.50 – 3.99 | 1 (lesson_04_statistics) |
| 3.00 – 3.49 | 6 (lesson_02_recursion, lesson_03_matrices, lesson_05_ml_basics, lesson_07_physics_momentum, lesson_08_history_dates, lesson_10_chemistry_balancing) |
| < 3.00 | 2 (lesson_01_derivatives, lesson_06_algebra) |

---

*Report auto-generated from 10 scored session files on 2026-03-12. Sessions stored in `sessions/`. Raw JSONL and scored JSONL available per session file.*
