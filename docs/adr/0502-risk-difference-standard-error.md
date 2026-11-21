# ADR 0502: The standard error of the risk difference

Status: accepted, 2026-11-20.

## Context

The risk difference (ADR 0501) is `p₁ − p₀` with `p₁ = TP/(TP + FP)` and
`p₀ = FN/(FN + TN)`. Its large-sample (Wald) standard error is
`sqrt(p₁(1 − p₁)/(TP + FP) + p₀(1 − p₀)/(FN + TN))`, which is
`sqrt(TP·FP/(TP + FP)³ + FN·TN/(FN + TN)³)`.

## Decision

- **The API.**
  - Python: `risk_difference_standard_error(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.RiskDifferenceStandardError(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Each term is formed from exact integers: `TP·FP` over `(TP + FP)³`, and `FN·TN` over
    `(FN + TN)³`, each integer converted to a double once and divided; the two terms are
    added and the square root taken.
  - At least 0, at most `sqrt(1/(4(TP + FP)) + 1/(4(FN + TN)))`. Unchanged when the truth
    is complemented.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A decision with no 1 or no 0 is an error, as for the risk difference.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, sums the two terms in rationals and takes
    the square root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
