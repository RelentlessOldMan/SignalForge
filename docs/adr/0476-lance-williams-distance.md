# ADR 0476: The Lance-Williams distance

Status: accepted, 2026-11-20.

## Context

The Lance-Williams distance of two binary records is `(FN + FP) / (2·TP + FN + FP)`: the
Bray-Curtis dissimilarity of two 0/1 records, and 1 less the Dice coefficient. 0 when the
records are equal, 1 when they share no 1.

## Decision

- **The API.**
  - Python: `lance_williams_distance(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.LanceWilliamsDistance(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `FN + FP` and `2·TP + FN + FP` are each converted to a double once;
    then one division.
  - From 0 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Both records all 0 is an error: the denominator is then 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
