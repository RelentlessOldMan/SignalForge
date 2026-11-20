# ADR 0472: The size difference

Status: accepted, 2026-11-20.

## Context

The size difference of two binary records is `(FN + FP)² / n²`: the square of the share of
items where they disagree, a dissimilarity. 0 when the records are equal, 1 when they are
opposite.

## Decision

- **The API.**
  - Python: `size_difference(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.SizeDifference(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `(FN + FP)²` and `n²` are each converted to a double once; then one
    division.
  - From 0 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Constant records are allowed.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
