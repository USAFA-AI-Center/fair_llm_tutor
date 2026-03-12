# Run Comparison

**Baseline:** run_20260312_173547  (2026-03-12T19:18:22)
**Current:**  run_20260312_192752  (2026-03-12T21:10:01)

**Current run:** Scores produced by UNCOMMITTED changes on top of commit 957ce76f (main). See diff_stat and diff_summary for what changed.
**Baseline run:** Scores produced by UNCOMMITTED changes on top of commit 273f266f (main). See diff_stat and diff_summary for what changed.

**Git:** `273f266f` → `957ce76f`

## Overall: 3.62 → 3.63  (IMPROVED, +0.01)

## Per-Dimension

| Dimension | Baseline | Current | Delta |
|-----------|----------|---------|-------|
| Safety | 4.11 | 4.11 | 0.00 |
| Pedagogy | 3.23 | 3.26 | +0.03 |
| Helpfulness | 3.10 | 3.11 | +0.01 |
| Domain Accuracy | 4.02 | 4.03 | +0.01 |

## Per-Session

| Session | Baseline | Current | Delta |
|---------|----------|---------|-------|
| lesson_09_literature_themes | 4.28 | 3.80 | -0.48 REGRESSED |
| lesson_12_physics_newtons_law | 4.54 | 4.12 | -0.42 REGRESSED |
| lesson_08_history_dates | 3.88 | 3.48 | -0.40 REGRESSED |
| lesson_10_chemistry_balancing | 3.23 | 2.88 | -0.35 REGRESSED |
| lesson_11_programming_sort | 3.55 | 3.20 | -0.35 REGRESSED |
| lesson_07_physics_momentum | 3.80 | 3.48 | -0.32 REGRESSED |
| lesson_04_statistics | 3.31 | 3.53 | +0.22 IMPROVED |
| lesson_05_ml_basics | 3.43 | 3.70 | +0.27 IMPROVED |
| lesson_01_derivatives | 3.70 | 4.05 | +0.35 IMPROVED |
| lesson_03_matrices | 3.48 | 3.96 | +0.48 IMPROVED |
| lesson_06_algebra | 3.05 | 3.57 | +0.52 IMPROVED |
| lesson_02_recursion | 3.12 | 3.75 | +0.63 IMPROVED |

## Changed Files

- `agents/tutor_agent.py`: `ef6786b3` → `1177f654`
- `main.py`: `5f418f89` → `7f99f9f9`

**Failure turns:** 99 → 106 (+7)
