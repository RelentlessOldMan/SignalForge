# ADR 0433: The Baroni-Urbani-Buser coefficient

Status: accepted, 2026-11-19.

## Context

The Baroni-Urbani-Buser coefficient of two binary records is
`(√(TP·TN) + TP) / (√(TP·TN) + TP + FN + FP)`. It is the Jaccard index (ADR 0388) with the
items both records mark 0 let in through the geometric mean `√(TP·TN)`: shared absences
count, but less than shared presences. It equals the Jaccard index when no item is 0 in
both, and is never below it.

## Decision

- **The API.**
  - Python: `baroni_urbani_buser_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.BaroniUrbaniBuserCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP·TN` an exact integer, converted to a double once (exact below `2⁵³`) and rooted once
    to `r`; `TP + FN + FP` an exact integer `k`. Then `(r + TP) / (r + k)`: the same
    operations in the same order in both languages.
  - From 0 to 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Both records all 0 is an error: `r + k = 0`.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
