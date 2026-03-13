# Run Comparison

**Baseline:** run_20260313_153916  (2026-03-13T17:23:58)
**Current:**  run_20260313_173441  (2026-03-13T19:19:08)

**Current run:** Scores produced by UNCOMMITTED changes on top of commit dcfbe2ad (main). See diff_stat and diff_summary for what changed.
**Baseline run:** Scores produced by UNCOMMITTED changes on top of commit 655d2ea9 (main). See diff_stat and diff_summary for what changed.

**Git:** `655d2ea9` → `dcfbe2ad`

## Overall: 3.69 → 3.72  (IMPROVED, +0.03)

## Per-Dimension

| Dimension | Baseline | Current | Delta |
|-----------|----------|---------|-------|
| Safety | 4.31 | 4.28 | -0.03 |
| Pedagogy | 3.37 | 3.56 | +0.19 |
| Helpfulness | 3.03 | 3.14 | +0.11 |
| Domain Accuracy | 4.03 | 3.90 | -0.13 |

## Per-Session

| Session | Baseline | Current | Delta |
|---------|----------|---------|-------|
| lesson_11_programming_sort | 4.03 | 3.45 | -0.58 REGRESSED |
| lesson_07_physics_momentum | 3.73 | 3.30 | -0.43 REGRESSED |
| lesson_08_history_dates | 3.75 | 3.43 | -0.32 REGRESSED |
| lesson_02_recursion | 3.73 | 3.42 | -0.31 REGRESSED |
| lesson_09_literature_themes | 4.37 | 4.22 | -0.15 |
| lesson_04_statistics | 3.76 | 3.65 | -0.11 |
| lesson_06_algebra | 3.50 | 3.55 | +0.05 |
| lesson_01_derivatives | 3.81 | 3.87 | +0.06 |
| lesson_03_matrices | 3.55 | 3.75 | +0.20 IMPROVED |
| lesson_13_quadratic_adversarial | 3.17 | 3.46 | +0.29 IMPROVED |
| lesson_10_chemistry_balancing | 3.03 | 3.53 | +0.50 IMPROVED |
| lesson_05_ml_basics | 3.88 | 4.42 | +0.54 IMPROVED |
| lesson_12_physics_newtons_law | 3.60 | 4.30 | +0.70 IMPROVED |

## Changed Files

- `agents/tutor_agent.py`: `aef12bff` → `130a19fb`
- `main.py`: `2225cc11` → `cbb69978`

**Failure turns:** 101 → 97 (-4)
