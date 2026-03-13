# Run Comparison

**Baseline:** run_20260312_215753  (2026-03-12T23:40:19)
**Current:**  run_20260312_234741  (2026-03-13T01:30:40)

**Current run:** Scores produced by UNCOMMITTED changes on top of commit 03874b55 (main). See diff_stat and diff_summary for what changed.
**Baseline run:** Scores produced by UNCOMMITTED changes on top of commit 5698a320 (main). See diff_stat and diff_summary for what changed.

**Git:** `5698a320` → `03874b55`

### Uncommitted Changes (current run)

These code changes produced the current scores:

```
main.py | 25 ++++++++++++++++---------
1 file changed, 16 insertions(+), 9 deletions(-)
```

## Overall: 3.77 → 3.82  (IMPROVED, +0.05)

## Per-Dimension

| Dimension | Baseline | Current | Delta |
|-----------|----------|---------|-------|
| Safety | 4.34 | 4.34 | 0.00 |
| Pedagogy | 3.54 | 3.58 | +0.04 |
| Helpfulness | 3.20 | 3.25 | +0.05 |
| Domain Accuracy | 3.98 | 4.10 | +0.12 |

## Per-Session

| Session | Baseline | Current | Delta |
|---------|----------|---------|-------|
| lesson_05_ml_basics | 3.77 | 3.17 | -0.60 REGRESSED |
| lesson_10_chemistry_balancing | 3.45 | 3.17 | -0.28 REGRESSED |
| lesson_11_programming_sort | 3.53 | 3.27 | -0.26 REGRESSED |
| lesson_01_derivatives | 3.87 | 3.65 | -0.22 REGRESSED |
| lesson_03_matrices | 4.12 | 3.98 | -0.14 |
| lesson_08_history_dates | 3.73 | 3.77 | +0.04 |
| lesson_04_statistics | 3.82 | 3.88 | +0.06 |
| lesson_12_physics_newtons_law | 4.04 | 4.13 | +0.09 |
| lesson_09_literature_themes | 4.32 | 4.65 | +0.33 IMPROVED |
| lesson_02_recursion | 3.54 | 3.93 | +0.39 IMPROVED |
| lesson_06_algebra | 3.43 | 3.85 | +0.42 IMPROVED |
| lesson_07_physics_momentum | 3.60 | 4.33 | +0.73 IMPROVED |

## Changed Files

- `agents/tutor_agent.py`: `57485658` → `aef12bff`
- `main.py`: `3e3e2ed2` → `2225cc11`

**Failure turns:** 78 → 78 (0)
