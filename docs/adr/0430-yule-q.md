# ADR 0430: Yule's Q

Status: accepted, 2026-11-19.

## Context

Yule's Q measures the association of two binary records from their 2×2 table:
`(TP·TN − FN·FP) / (TP·TN + FN·FP)`. With the odds ratio `OR = TP·TN / (FN·FP)` it is
`(OR − 1) / (OR + 1)`, so it maps the diagnostic odds ratio already built onto `[−1, 1]`:
1 when either mismatch cell is empty, −1 when either match cell is empty,
0 for no association. Unlike the odds ratio it stays finite when a cell is empty.

## Decision

- **The API.**
  - Python: `yule_q(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.YuleQ(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP`, `FN`, `FP`, `TN` the four counts; `x = TP·TN`, `y = FN·FP` as exact integers.
  - `(x − y) / (x + y)`: each integer is converted to a double once, then one division.
    Both are exact below `2⁵³`, which holds for any record shorter than `2²⁷` items.
  - From −1 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `x + y = 0` is an error: no product has both its cells filled, so there is no
    association to measure (a record that is constant, for one).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
