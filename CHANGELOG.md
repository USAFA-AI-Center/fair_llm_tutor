# Changelog

All notable changes to the fair_llm_tutor project are documented here.

---

## [Unreleased] — 2026-03-12 (Run #5)

Targeted improvements driven by run `run_20260312_215753` (12/17 scenarios).
Previous run: **3.63/5.00** → Current run: **3.77/5.00** (+0.14).
Focus: catching single-word praise confirmations, preventing context/topic drift, and making responses more specific and actionable.

### Safety (P0) — 22 failure turns

- **Expanded praise confirmation filter** (`main.py:160-167`): Added single-word/short-phrase confirmations to `_PRAISE_CONFIRMATION_RE`: "Exactly!", "Right!", "Yes!", "Absolutely!", "You're right/correct", "That's right/correct/it", "Spot on!", "Nailed it!", "Bingo!". Why: these short affirmations were slipping through the existing filter which only caught multi-word praise phrases.

- **Added mid-sentence affirmation stripping** (`main.py:341-349`): New regex strips "Exactly.", "Precisely,", "You're correct" when embedded mid-sentence. Why: even after the start-of-response filter, single-word confirmations appeared mid-response (e.g., "Exactly, that's the right approach.").

- **Expanded confirmation discipline in prompt** (`agents/tutor_agent.py:444-446`): Added explicit prohibition of "Exactly!", "Correct!", "Right!", "That's it!", "Spot on!", "Bingo!" and all single-word/short-phrase affirmations. Why: the LLM needed clearer instruction that ANY short affirmation confirms correctness.

### Correctness (P1) — 27 failure turns

- **Strengthened context drift prevention** (`agents/tutor_agent.py:394-398`): Added rules prohibiting introduction of new variables/functions not in the original problem (e.g., inventing g(x) when problem uses f(x)), and requiring examples/analogies to use different numbers from the same problem type. Why: lesson_01_derivatives showed the tutor introducing g(x) and h(x) functions, and lesson_02_recursion drifted from factorial to fibonacci.

- **Improved student drift redirection** (`agents/tutor_agent.py:390-391`): Changed generic "redirect them back" to specific template: "Let's come back to [current problem]. We can explore that other topic after we finish this one." Why: the tutor acknowledged drift but didn't actively redirect.

### Pedagogy (P2) — 39 failure turns + 59 helpfulness failures

- **Added response advancement rule** (`agents/tutor_agent.py:433-436`): New rule requires every response to advance the student's understanding with something NEW — a new angle, a specific step to examine, or a concrete sub-problem. Prohibits repeating the same question in different words. Why: multiple sessions showed the tutor asking the same question 3+ times in different phrasing.

- **Added specificity rule** (`agents/tutor_agent.py:437-439`): New rule requires specific references to the student's work instead of generic phrases. Example: "Look at the step where you multiplied — what rule did you apply there?" instead of "Check your work". Why: generic responses scored low on both pedagogy and helpfulness.

- **Improved neutral openers** (`main.py:170-177`): Expanded from 5 to 8 openers, replaced vague "Let's focus on the key step in your work" with more engaging alternatives like "Interesting approach — let me ask you about one specific step" and "There's a key detail here worth revisiting". Why: the original openers were too generic and contributed to helpfulness failures.

---

## [Unreleased] — 2026-03-12 (Run #4)

Targeted improvements driven by run `run_20260312_192752` (12/17 scenarios).
Previous run: **3.62/5.00** → Current run: **3.63/5.00** (+0.01).
Focus: catching missed answer confirmation patterns, improving calculation leakage detection, and making replacement phrases more pedagogically useful.

### Safety (P0) — 34 failure turns

- **Expanded confirmation verbs** (`main.py`): Added `recalculated`, `recalculating`, `completed`, `established`, `proved`, `proven`, `obtained`, `arrived` to `_CONFIRMATION_VERBS`. Why: "You have correctly recalculated the top-left element as 19" slipped through because `recalculated` was not in the verb list (lesson_03_matrices turn 9).

- **Added praise-value confirmation filter** (`main.py`): New `_PRAISE_VALUE_RE` catches patterns like "Great job on recalculating the top-right element correctly as 22!" — praise followed by embedded value confirmation. Why: lesson_03_matrices turn 8 flagged for confirming specific numeric values within praise phrases.

- **Added complete calculation filter** (`main.py`): New `_COMPLETE_CALCULATION_RE` catches step-by-step calculations that reveal intermediate and final values (e.g., "3×6 + 4×8 = 18 + 32 = 50"). Why: lesson_03_matrices turn 9 revealed the bottom-right element by showing the full calculation chain.

- **Expanded direct answer detection** (`main.py`): `_DIRECT_ANSWER_RE` now matches "your [final] result/answer is" and "is approximately" patterns. Also added "completed" to `_IMPLICIT_CONFIRMATION_RE` and "your final/complete result is" clause. Why: "Your final result is approximately 2.14" (lesson_04_statistics turn 4) and "the original standard deviation was around 2.14" (turn 5) slipped through.

### Pedagogy (P2) — 51 failure turns + 59 helpfulness failures

- **Improved replacement phrases** (`main.py`): Rewrote all `_CONFIRMATION_REPLACEMENTS`, `_DIRECT_ANSWER_REPLACEMENTS`, and `_NEUTRAL_OPENERS` to be more substantive and pedagogically useful. Old phrases were generic and disconnected ("How does this connect to what we discussed earlier?", "Can you think of a case where this approach might not work?"). New phrases prompt specific reasoning steps ("Let's check your reasoning step by step — what was the first operation you performed, and why?"). Why: the judge scored replacement-generated responses low on both pedagogy and helpfulness because they didn't engage with the student's actual work (lesson_01_derivatives turns 5-7).

- **Strengthened Socratic teaching rules** (`agents/tutor_agent.py`): Added requirement that responses must END with a question, and that explanations longer than 2 sentences must be interspersed with questions. Why: lesson_02_recursion turns 14-15 showed the tutor lecturing about recursion vs iteration for multiple sentences without asking any questions.

- **Tighter context management** (`agents/tutor_agent.py`): Added rules to never introduce topics the student didn't ask about, and to keep follow-up questions on the same problem/topic. Why: lesson_05_ml_basics turn 6 — tutor drifted to dimensionality reduction when the problem was about supervised vs unsupervised learning.

---

## [Unreleased] — 2026-03-12 (Run #3)

Targeted improvements driven by run `run_20260312_173547` (12/17 scenarios).
Previous run: **3.51/5.00** → Current run: **3.62/5.00** (+0.11).
Focus: breaking the repetitive "walk me through your steps" loop, catching implicit answer confirmations, and preventing code solution leaks.

### Safety (P0) — 35 failure turns

- **Added implicit confirmation filter** (`main.py`): New `_IMPLICIT_CONFIRMATION_RE` catches phrases like "your function should work perfectly", "Here's your final code:", "Your final implementation is:" that confirm correctness without explicitly stating the answer. Why: 35 turns scored safety <= 2; the judge flagged "your function should work perfectly" and "Here's your final code:" as implicit answer revelations (lesson_02_recursion turns 4, 6, 9, 10).

- **Added code block solution stripping** (`main.py`): New regex in `sanitize_tutor_response()` strips complete code blocks that follow confirmatory phrasing (e.g., "Here's your code: ```python...```"). Why: the tutor was dumping full working implementations as "final code" which reveals the answer.

### Pedagogy (P2) — 63 failure turns + 72 helpfulness failures

- **Diversified replacement phrases** (`main.py`): Replaced all 5 `_CONFIRMATION_REPLACEMENTS` (previously all variants of "walk me through your steps") with 7 genuinely different question types: "What rule did you apply?", "What if the input were different?", "Can you think of a case where this wouldn't work?", etc. Also diversified `_DIRECT_ANSWER_REPLACEMENTS`. Why: the post-processor was creating an inescapable repetition loop — it stripped praise/confirmations and replaced them with "walk me through your steps", which the LLM then echoed back, causing 63 pedagogy and 72 helpfulness failures.

- **Stronger anti-repetition rules** (`agents/tutor_agent.py`): Replaced general anti-repetition guidance with an explicit BANNED PHRASES list ("walk me through", "explain your reasoning", "show me your work", "what method did you use"). Added instruction to never provide complete code solutions. Why: lesson_01_derivatives had 14 failure turns where the tutor repeated "walk me through your steps" on turns 4-17 despite the student's increasing frustration.

- **Improved frustration handling** (`agents/tutor_agent.py`): Rewrote the frustration handling rule to be more direct: if the student expresses frustration, YOU are the problem. Must immediately give a concrete, specific hint about content — not another meta-question about process. Why: lesson_01_derivatives turns 9-17 show escalating student frustration with the tutor repeatedly asking the same question.

- **Strengthened context management** (`agents/tutor_agent.py`): Added instruction to reference the current problem BY NAME in every response, and to READ the PROBLEM field from input carefully. Why: lesson_02_recursion turn 13 — tutor responded about sum of squares when the problem was factorial.

---

## [Unreleased] — 2026-03-12 (Run #2)

Targeted improvements driven by run `run_20260312_153752` (13/17 scenarios).
Baseline score: **3.35/5.00** → Previous run: **3.51/5.00** (+0.16).

### Safety (P0) — 41 failure turns

- **Added standalone praise filter** (`main.py`): New `_PRAISE_CONFIRMATION_RE` catches response-initial praise ("Excellent work!", "Great job!", "Well done!") that implicitly confirms a student's answer even without stating it. Replaced with neutral openers from `_NEUTRAL_OPENERS` list. Why: 41 turns scored safety <= 2; the judge flagged "Excellent work!" as implicit answer confirmation even when no explicit answer was stated.

- **Strengthened confirmation discipline in prompt** (`agents/tutor_agent.py`): Added explicit instruction to NEVER start responses with praise unless `check_student_history` confirmed AND student explained reasoning. Instructs tutor to lead with substance ("Let's look at your approach...") instead of evaluative praise. Why: the tutor reflexively opened with "Great job!" which the judge treats as confirming correctness.

### Correctness (P1) — 45 failure turns

- **Strengthened context management** (`agents/tutor_agent.py`): Added two new rules: (1) "STAY ON THE ASSIGNED PROBLEM" — redirect students who drift to different problems (e.g., fibonacci when assignment is factorial); (2) After marking a problem solved, explicitly state the NEW problem before asking questions — never say "walk me through your steps for this one" without specifying which problem. Why: 45 turns scored domain_accuracy <= 2, primarily from the tutor following student tangents to unrelated problems or failing to specify the current problem after transitions.

### Pedagogy (P2) — 54 failure turns + 66 helpfulness failures

- **Anti-repetition overhaul** (`agents/tutor_agent.py`): Added explicit instruction to NEVER say "walk me through your steps" or "can you explain your reasoning" more than once per conversation. Added varied question form suggestions. Why: the derivatives session showed 6+ consecutive "walk me through your steps" turns, causing both pedagogy and helpfulness failures.

- **Confusion handling** (`agents/tutor_agent.py`): Strengthened instructions for when students say "I'm confused" or "I already explained that" — tutor must stop current approach, restate the problem, and offer a concrete starting point instead of repeating the same question. Why: helpfulness failures (-0.11 regression) were driven by the tutor ignoring student confusion signals.

---

## [Unreleased] — 2026-03-11

Targeted improvements driven by the automated evaluation pipeline (`student_mode/pipeline.py`).
Baseline score: **3.35/5.00** across 17 scenarios. Last evaluated: **3.44/5.00** (+0.09).

### Safety (P0) — 46 failure turns in baseline

- **Consolidated answer-confirmation filter** (`main.py`): Merged `_PRAISE_WITH_ANSWER_RE` into `_ANSWER_CONFIRMATION_RE` using a shared `_CONFIRMATION_VERBS` constant. The unified pattern now catches both praise-prefixed confirmations ("Great job! You correctly found X") and standalone confirmations ("You correctly derived h'(x) = ...") with verbs `applied` and `shown` added. Why: the two patterns had overlapping verb lists maintained independently, and the standalone form was slipping through the old filter.

- **Added direct-answer filter** (`main.py`): New `_DIRECT_ANSWER_RE` catches tutor responses that state answers directly ("the answer is 42", "simplifies to 6x + 2", "is indeed x = 6"). Requires a digit or `=` sign after the trigger phrase to avoid false positives on Socratic questions like "Does the answer match what you expected?" Why: 46 turns in the baseline scored safety <= 2, many from the tutor stating the answer outright rather than confirming a student's correct work.

- **Extracted `_DIRECT_ANSWER_REPLACEMENT` constant** (`main.py`): The replacement string used by the direct-answer filter is now a named module-level constant alongside `_CONFIRMATION_REPLACEMENT`. Why: consistency with the existing pattern and central updateability.

### Pedagogy (P2) — 67 failure turns in baseline

- **Added SOCRATIC TEACHING RULES to agent prompt** (`agents/tutor_agent.py`): New prompt section instructs the tutor to always include at least one question, break concepts into smaller pieces for confused students, build on partial understanding, never ignore student confusion, and prefer guided discovery over lecturing. Why: the judge flagged 67 turns for pedagogy <= 2, primarily from the tutor giving direct instruction rather than asking Socratic questions.

### Bugfix

- **Fixed `sys.executable` in session runner** (`student_mode/runner.py`): Replaced hardcoded `"python"` with `sys.executable` so the runner uses the active virtual environment's interpreter. Why: the pipeline failed to start sessions when `python` wasn't on `PATH` (only the venv's full path was available).
