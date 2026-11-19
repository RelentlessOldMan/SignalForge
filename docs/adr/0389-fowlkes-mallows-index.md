# ADR 0389: The Fowlkes–Mallows index

Status: accepted, 2026-11-19.

## Context

Fowlkes and Mallows (1983) compared two clusterings by the geometric mean of two
conditional rates. For a binary decision against the truth it is the geometric mean of
precision and recall, a companion to the F1 score (ADR 0386), their harmonic mean.

## Decision

- **The API.**
  - Python: `fowlkes_mallows_index(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.FowlkesMallowsIndex(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
  - The records as for the Matthews correlation (ADR 0385): 0 and 1, 1 positive.
  - Only the binary form is built; the form over two clusterings of pairs is not.
- **The value.**
  - `FM = TP/√((TP + FP)(TP + FN))`, from 0 to 1. The product is formed in `double`, its
    root taken, then the division done.
  - It is symmetric in the two records.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1, every value 0 or 1.
  - `TP + FP > 0` and `TP + FN > 0`: a 1 in each record.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts in integers and takes one correctly rounded root of the exact
    product.
  - The tolerance is `abs 1e-15, rel 1e-14`.
