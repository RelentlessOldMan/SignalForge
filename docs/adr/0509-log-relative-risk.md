# ADR 0509: The log relative risk

Status: accepted, 2026-11-20.

## Context

The relative risk (ADR 0484) is `P / Q` with `P = TP·(FN + TN)` and `Q = FN·(TP + FP)`.
Its standard error (ADR 0499) and Wald z (ADR 0500) are for its logarithm, which is
symmetric about 0 where the relative risk is not about 1.

## Decision

- **The API.**
  - Python: `log_relative_risk(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.LogRelativeRisk(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `ln(P/Q)`: the exact integers `P` and `Q` are each converted to a double once, then
    one division and the logarithm.
  - Any real value; 0 exactly when `P = Q`.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - TP = 0 or FN = 0 is an error: the logarithm of 0 or of an infinite ratio. A decision
    with no 1 has TP = 0, so it is an error too.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the logarithm of the exact ratio in
    40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
