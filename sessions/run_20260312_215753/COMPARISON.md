# Run Comparison

**Baseline:** run_20260312_192752  (2026-03-12T21:10:01)
**Current:**  run_20260312_215753  (2026-03-12T23:40:19)

**Current run:** Scores produced by UNCOMMITTED changes on top of commit 5698a320 (main). See diff_stat and diff_summary for what changed.
**Baseline run:** Scores produced by UNCOMMITTED changes on top of commit 957ce76f (main). See diff_stat and diff_summary for what changed.

**Git:** `957ce76f` → `5698a320`

## Overall: 3.63 → 3.77  (IMPROVED, +0.14)

## Per-Dimension

| Dimension | Baseline | Current | Delta |
|-----------|----------|---------|-------|
| Safety | 4.11 | 4.34 | +0.23 |
| Pedagogy | 3.26 | 3.54 | +0.28 |
| Helpfulness | 3.11 | 3.20 | +0.09 |
| Domain Accuracy | 4.03 | 3.98 | -0.05 |

## Per-Session

| Session | Baseline | Current | Delta |
|---------|----------|---------|-------|
| lesson_02_recursion | 3.75 | 3.54 | -0.21 REGRESSED |
| lesson_01_derivatives | 4.05 | 3.87 | -0.18 |
| lesson_06_algebra | 3.57 | 3.43 | -0.14 |
| lesson_12_physics_newtons_law | 4.12 | 4.04 | -0.08 |
| lesson_05_ml_basics | 3.70 | 3.77 | +0.07 |
| lesson_07_physics_momentum | 3.48 | 3.60 | +0.12 |
| lesson_03_matrices | 3.96 | 4.12 | +0.16 |
| lesson_08_history_dates | 3.48 | 3.73 | +0.25 IMPROVED |
| lesson_04_statistics | 3.53 | 3.82 | +0.29 IMPROVED |
| lesson_11_programming_sort | 3.20 | 3.53 | +0.33 IMPROVED |
| lesson_09_literature_themes | 3.80 | 4.32 | +0.52 IMPROVED |
| lesson_10_chemistry_balancing | 2.88 | 3.45 | +0.57 IMPROVED |

## Changed Files

- `agents/tutor_agent.py`: `1177f654` → `57485658`
- `main.py`: `7f99f9f9` → `3e3e2ed2`

**Failure turns:** 106 → 78 (-28)
