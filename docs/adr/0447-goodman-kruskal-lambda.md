# ADR 0447: Goodman and Kruskal's lambda

Status: accepted, 2026-11-19.

## Context

Goodman and Kruskal's lambda measures how many of the errors made in guessing a record by its
most common value are removed by knowing the other record. For two binary records the
symmetric lambda, both directions pooled, is `(σ − σ') / (2n − σ')` with
`σ = max(TP, FN) + max(FP, TN) + max(TP, FP) + max(FN, TN)` and
`σ' = max(|A|, n − |A|) + max(|B|, n − |B|)`, the same sums as Anderberg's D (ADR 0446),
which divides by `2n` instead. From 0 (no errors removed, which includes independence) to 1
(each record fixes the other).

## Decision

- **The API.**
  - Python: `goodman_kruskal_lambda(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.GoodmanKruskalLambda(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
  - Only the symmetric lambda; the two one-way lambdas are not separate functions.
- **The value.**
  - `σ − σ'` and `2n − σ'` are exact integers, each converted to a double once, then one
    division.
  - From 0 to 1. Symmetric in the two records; unchanged when either record is flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `σ' = 2n` is an error: then both records are constant and there is no error to remove.
    One constant record alone is not an error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from the
    cell shares, as row and column maxima.
  - The tolerance is `abs 1e-15, rel 1e-15`.
