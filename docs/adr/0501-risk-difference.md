# ADR 0501: The risk difference

Status: accepted, 2026-11-20.

## Context

With the decision as the exposure, as for the relative risk (ADR 0484), the risk
difference is the share of truth 1s where the decision is 1 minus the share where it is
0: `TP/(TP + FP) − FN/(FN + TN)`. Over a common denominator it is
`(TP·TN − FN·FP) / ((TP + FP)·(FN + TN))`.

## Decision

- **The API.**
  - Python: `risk_difference(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.RiskDifference(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP·TN − FN·FP` and `(TP + FP)·(FN + TN)` are each converted to a
    double once, then one division.
  - From −1 to 1; 0 when the two shares are equal. It changes sign when the truth is
    complemented.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A decision with no 1 or no 0 is an error: one of the shares is then undefined.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the difference in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
