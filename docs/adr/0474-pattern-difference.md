# ADR 0474: The pattern difference

Status: accepted, 2026-11-20.

## Context

The pattern difference of two binary records is `4·FN·FP / n²`, a dissimilarity: four
times the product of the shares of the two kinds of disagreement. 0 when the records
disagree only one way, 1 when half the items are FN and half FP.

## Decision

- **The API.**
  - Python: `pattern_difference(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.PatternDifference(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `4·FN·FP` and `n²` are each converted to a double once; then one
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
