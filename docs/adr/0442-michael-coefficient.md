# ADR 0442: Michael's coefficient

Status: accepted, 2026-11-19.

## Context

Michael's coefficient of two binary records is
`4·(TP·TN − FN·FP) / ((TP + TN)² + (FN + FP)²)`: the cross-product difference of the 2x2
table over the squares of the agreements and the disagreements. 1 when the records agree
everywhere, −1 when they disagree everywhere, 0 for `TP·TN = FN·FP`. Since
`(TP + TN) + (FN + FP) = n`, the denominator is at least `n²/2`, so the value is defined for
every pair of valid records, constant ones included.

## Decision

- **The API.**
  - Python: `michael_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.MichaelCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The numerator and the denominator are exact integers, each converted to a double once
    (exact below `2⁵³`, which holds for any record shorter than `2²⁶` items), then one
    division.
  - From −1 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No further error: the denominator is never zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from the
    cell shares.
  - The tolerance is `abs 1e-15, rel 1e-15`.
