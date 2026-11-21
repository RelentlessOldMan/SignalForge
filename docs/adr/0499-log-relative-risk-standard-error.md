# ADR 0499: The standard error of the log relative risk

Status: accepted, 2026-11-20.

## Context

The relative risk (ADR 0484) takes the decision as the exposure:
`(TP / (TP + FP)) / (FN / (FN + TN))`. The large-sample (delta-method) standard error of
its logarithm is `sqrt(1/TP − 1/(TP + FP) + 1/FN − 1/(FN + TN))`, which is
`sqrt(FP / (TP·(TP + FP)) + TN / (FN·(FN + TN)))`.

## Decision

- **The API.**
  - Python: `log_relative_risk_standard_error(truth, decision)` in `measurements`, giving
    a float.
  - C#: `Measurements.LogRelativeRiskStandardError(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The sum is the exact rational
    `(FP·FN·(FN + TN) + TN·TP·(TP + FP)) / (TP·(TP + FP)·FN·(FN + TN))`; its numerator and
    denominator are each converted to a double once, then one division and the square
    root.
  - At least 0; 0 exactly when FP = TN = 0 (every record has truth 1).
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - TP = 0 or FN = 0 is an error: the log relative risk is then not finite.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, sums the two terms in rationals and takes
    the square root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
