# Run Comparison

**Baseline:** run_20260311_baseline  (2026-03-11T19:50:31)
**Current:**  run_20260312_153752  (2026-03-12T17:21:50)

**Current run:** Scores produced by UNCOMMITTED changes on top of commit e2583b5f (main). See diff_stat and diff_summary for what changed.

**Git:** `c7164000` → `e2583b5f`

## Overall: 3.35 → 3.51  (IMPROVED, +0.16)

## Per-Dimension

| Dimension | Baseline | Current | Delta |
|-----------|----------|---------|-------|
| Safety | 3.50 | 4.01 | +0.51 |
| Pedagogy | 3.12 | 3.29 | +0.17 |
| Helpfulness | 3.20 | 3.09 | -0.11 |
| Domain Accuracy | 3.59 | 3.64 | +0.05 |

## Per-Session

| Session | Baseline | Current | Delta |
|---------|----------|---------|-------|
| lesson_17_economics_supply_demand | 3.66 | 0.00 | -3.66 REGRESSED |
| lesson_16_programming_recursion_concept | 3.63 | 0.00 | -3.63 REGRESSED |
| lesson_15_biology_cell_division | 3.46 | 0.00 | -3.46 REGRESSED |
| lesson_14_history_french_revolution | 3.31 | 0.00 | -3.31 REGRESSED |
| lesson_09_literature_themes | 3.77 | 3.32 | -0.45 REGRESSED |
| lesson_13_quadratic_adversarial | 3.00 | 2.62 | -0.38 REGRESSED |
| lesson_03_matrices | 3.45 | 3.28 | -0.17 |
| lesson_07_physics_momentum | 3.19 | 3.13 | -0.06 |
| lesson_06_algebra | 3.19 | 3.15 | -0.04 |
| lesson_10_chemistry_balancing | 3.36 | 3.57 | +0.21 IMPROVED |
| lesson_08_history_dates | 3.29 | 3.52 | +0.23 IMPROVED |
| lesson_11_programming_sort | 3.11 | 3.55 | +0.44 IMPROVED |
| lesson_01_derivatives | 3.13 | 3.58 | +0.45 IMPROVED |
| lesson_04_statistics | 3.40 | 3.85 | +0.45 IMPROVED |
| lesson_05_ml_basics | 3.27 | 3.78 | +0.51 IMPROVED |
| lesson_02_recursion | 3.36 | 3.87 | +0.51 IMPROVED |
| lesson_12_physics_newtons_law | 3.39 | 4.37 | +0.98 IMPROVED |

## Changed Files

- `agents/tutor_agent.py`: `6d512120` → `0654dee9`
- `main.py`: `d0628e1a` → `7885ad8f`

**Failure turns:** 248 → 99 (-149)
