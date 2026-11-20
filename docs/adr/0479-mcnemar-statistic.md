# ADR 0479: McNemar's statistic

Status: accepted, 2026-11-20.

## Context

McNemar's statistic for two paired binary records is `(FN − FP)² / (FN + FP)`, without
continuity correction: it tests whether the two kinds of disagreement are equally common.
0 when they are, `FN + FP` when the records disagree one way only.

## Decision

- **The API.**
  - Python: `mcnemar_statistic(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.McNemarStatistic(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `(FN − FP)²` and `FN + FP` are each converted to a double once; then
    one division.
  - At least 0, at most `n`. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Records that agree everywhere are an error: `FN + FP` is then 0.
  - No continuity correction.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
