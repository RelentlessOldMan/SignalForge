# ADR 0505: The relative risk reduction

Status: accepted, 2026-11-20.

## Context

The relative risk reduction is one minus the relative risk (ADR 0484): the share by which
the risk of a truth 1 falls among the exposed (decision 1) relative to the unexposed. Over
a common denominator it is `(FN·FP − TP·TN) / ((TP + FP)·FN)`.

## Decision

- **The API.**
  - Python: `relative_risk_reduction(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.RelativeRiskReduction(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `FN·FP − TP·TN` and `(TP + FP)·FN` are each converted to a double
    once, then one division.
  - At most 1, reached when the exposed have no truth 1; 0 when the two risks are equal;
    negative when the exposed risk is the larger.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - As for the relative risk: a decision with no 1, or `FN = 0`, is an error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and divides the two exact integers in
    40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
