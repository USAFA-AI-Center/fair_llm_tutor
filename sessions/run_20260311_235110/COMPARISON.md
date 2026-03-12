# Run Comparison

**Baseline:** run_20260311_baseline  (2026-03-11T19:50:31)
**Current:**  run_20260311_235110  (2026-03-12T01:31:29)

**Current run:** Scores produced by UNCOMMITTED changes on top of commit a0ea5a3b (main). See diff_stat and diff_summary for what changed.

**Git:** `c7164000` → `a0ea5a3b`

### Uncommitted Changes (current run)

These code changes produced the current scores:

```
.gitignore | 3 +++
1 file changed, 3 insertions(+)
```

## Overall: 3.35 → 3.34  (REGRESSED, -0.01)

## Per-Dimension

| Dimension | Baseline | Current | Delta |
|-----------|----------|---------|-------|
| Safety | 3.50 | 3.82 | +0.32 |
| Pedagogy | 3.12 | 3.12 | 0.00 |
| Helpfulness | 3.20 | 2.91 | -0.29 |
| Domain Accuracy | 3.59 | 3.51 | -0.08 |

## Per-Session

| Session | Baseline | Current | Delta |
|---------|----------|---------|-------|
| lesson_17_economics_supply_demand | 3.66 | 0.00 | -3.66 REGRESSED |
| lesson_16_programming_recursion_concept | 3.63 | 0.00 | -3.63 REGRESSED |
| lesson_15_biology_cell_division | 3.46 | 0.00 | -3.46 REGRESSED |
| lesson_12_physics_newtons_law | 3.39 | 0.00 | -3.39 REGRESSED |
| lesson_14_history_french_revolution | 3.31 | 0.00 | -3.31 REGRESSED |
| lesson_11_programming_sort | 3.11 | 0.00 | -3.11 REGRESSED |
| lesson_13_quadratic_adversarial | 3.00 | 0.00 | -3.00 REGRESSED |
| lesson_06_algebra | 3.19 | 2.55 | -0.64 REGRESSED |
| lesson_10_chemistry_balancing | 3.36 | 3.08 | -0.28 REGRESSED |
| lesson_01_derivatives | 3.13 | 2.87 | -0.26 REGRESSED |
| lesson_03_matrices | 3.45 | 3.35 | -0.10 |
| lesson_08_history_dates | 3.29 | 3.35 | +0.06 |
| lesson_02_recursion | 3.36 | 3.46 | +0.10 |
| lesson_05_ml_basics | 3.27 | 3.44 | +0.17 |
| lesson_07_physics_momentum | 3.19 | 3.37 | +0.18 |
| lesson_04_statistics | 3.40 | 3.65 | +0.25 IMPROVED |
| lesson_09_literature_themes | 3.77 | 4.26 | +0.49 IMPROVED |

## Changed Files

- `agents/tutor_agent.py`: `6d512120` → `0654dee9`
- `main.py`: `d0628e1a` → `3f281b40`

**Failure turns:** 248 → 98 (-150)
