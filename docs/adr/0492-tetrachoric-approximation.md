# ADR 0492: The tetrachoric approximation

Status: accepted, 2026-11-20.

## Context

Pearson's cosine approximation to the tetrachoric correlation of two binary records is
`cos(π / (1 + sqrt(OR)))` with the odds ratio `OR = TP·TN / (FN·FP)`. It runs from −1
(`OR = 0`) through 0 (`OR = 1`, independent records) towards 1 as `OR` grows. It is a quick
stand-in for the maximum likelihood tetrachoric correlation, which needs the bivariate
normal distribution.

## Decision

- **The API.**
  - Python: `tetrachoric_approximation(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.TetrachoricApproximation(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP·TN` and `FN·FP` are each converted to a double once; then one
    division, the square root, one addition of 1, π (the double nearest it) divided by the
    sum, and the cosine.
  - From −1 to 1, below 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `FN·FP = 0` is an error (the odds ratio is undefined or infinite).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and works in 40-digit decimals, with π from
    Machin's formula and the cosine from its Taylor series.
  - The tolerance is `abs 1e-13, rel 1e-13`.
