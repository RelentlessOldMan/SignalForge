# ADR 0388: The Jaccard index

Status: accepted, 2026-11-19.

## Context

Jaccard (1901) measured the overlap of two sets as the size of their intersection over the
size of their union. For a binary decision against the truth, the sets are the items each
calls positive: the index is the critical success index or threat score of forecasting, and
the intersection over union of segmentation.

## Decision

- **The API.**
  - Python: `jaccard_index(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.JaccardIndex(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
  - The records as for the Matthews correlation (ADR 0385): 0 and 1, 1 the member of the
    set. It is symmetric, so the names only say which record is which.
- **The value.**
  - `J = TP/(TP + FP + FN)`, from 0 to 1, a ratio of whole numbers.
  - It is a monotone function of the F1 score (ADR 0386): `F1 = 2J/(1 + J)`.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1, every value 0 or 1.
  - `TP + FP + FN > 0`: the union not empty.

## Consequences

- The cost is one pass.
- The weighted (Ruzicka) and real-valued forms are not built.
- **Vectors.**
  - The generator counts in integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
