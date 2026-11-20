# ADR 0484: The relative risk

Status: accepted, 2026-11-20.

## Context

The relative risk (risk ratio) treats the decision as an exposure and the truth as an
outcome: the share of 1s in truth where the decision is 1, `TP / (TP + FP)`, over the share
where it is 0, `FN / (FN + TN)`. That is `TP·(FN + TN) / ((TP + FP)·FN)`. 1 when the
records are independent.

## Decision

- **The API.**
  - Python: `relative_risk(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.RelativeRisk(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP·(FN + TN)` and `(TP + FP)·FN` are each converted to a double
    once; then one division.
  - At least 0. Not symmetric: `decision` gives the exposure groups.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A decision with no 1 is an error, and so is `FN = 0` (this covers a decision with
    no 0).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
