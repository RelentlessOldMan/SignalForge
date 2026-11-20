# ADR 0473: The shape difference

Status: accepted, 2026-11-20.

## Context

The shape difference of two binary records is `(n·(FN + FP) − (FN − FP)²) / n²`, a
dissimilarity: the share of disagreements less the squared imbalance between the two kinds
of disagreement. 0 when the records are equal, 1 when they are opposite with as many 1s as
0s turned each way.

## Decision

- **The API.**
  - Python: `shape_difference(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.ShapeDifference(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `n·(FN + FP) − (FN − FP)²` and `n²` are each converted to a double
    once; then one division.
  - From 0 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Constant records are allowed.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
