# ADR 0507: The standard error of Cohen's h

Status: accepted, 2026-11-20.

## Context

The arcsine square root transform stabilizes the variance of a share: `2·asin(√p̂)` from
`n` records has a large-sample variance of `1/n` whatever `p`. So Cohen's h (ADR 0506)
from two independent groups of `n₁ = TP + FP` and `n₂ = FN + TN` records has the
standard error `√(1/n₁ + 1/n₂)`.

## Decision

- **The API.**
  - Python: `cohen_h_standard_error(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.CohenHStandardError(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `1/n₁ + 1/n₂` is formed as the exact integer `n₁ + n₂` over the exact integer `n₁·n₂`,
    each converted to a double once; then one division and one square root.
  - Greater than 0 and at most `√2`. It depends only on how many 1s and 0s the decision
    holds, not on the truth.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A decision with no 1 or no 0 is an error, as for Cohen's h.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the decision's 1s and 0s directly, sums the two reciprocals in
    rationals and takes the square root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
