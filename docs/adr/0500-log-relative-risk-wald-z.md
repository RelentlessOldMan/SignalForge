# ADR 0500: The Wald z of the log relative risk

Status: accepted, 2026-11-20.

## Context

The relative risk (ADR 0484) is `P / Q` with `P = TP·(FN + TN)` and `Q = FN·(TP + FP)`.
The Wald statistic divides its logarithm by its standard error (ADR 0499), whose square
is `M / (PQ)` with `M = FP·FN·(FN + TN) + TN·TP·(TP + FP)`. So
`z = ln(P/Q)·sqrt(PQ / M)`.

## Decision

- **The API.**
  - Python: `log_relative_risk_wald_z(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.LogRelativeRiskWaldZ(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `ln(P/Q)·sqrt(PQ / M)`: the exact integers `P`, `Q`, `PQ` and `M` are each converted
    to a double once; one division and the logarithm, one division and the square root,
    then the product.
  - Any real value; 0 exactly when `P = Q`.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - TP = 0 or FN = 0 is an error, as for the standard error of the log relative risk.
  - `M = 0` (FP = TN = 0, every record has truth 1) is an error: the standard error is 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the logarithm and the square root in
    40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
