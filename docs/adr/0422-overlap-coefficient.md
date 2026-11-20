# ADR 0422: The overlap coefficient

Status: accepted, 2026-11-19.

## Context

The overlap coefficient (Szymkiewicz–Simpson) of two binary records is the number of items
both mark 1 over the smaller of the two counts of 1. It is 1 whenever one set holds the
other, which the Jaccard index (ADR 0388) is not: a detector that flags a subset of the true
events, or a superset, scores full overlap.

## Decision

- **The API.**
  - Python: `overlap_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.OverlapCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
  - The argument names follow the Jaccard index, though the coefficient is symmetric.
- **The value.**
  - `|A ∩ B| / min(|A|, |B|)`, with `A` and `B` the items each record marks 1; the counts are
    integers and the quotient is one division.
  - From 0 to 1; 1 when one set holds the other.
- **The rules.**
  - As for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Either record with no 1 is an error: the smaller count is zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly; the value is a ratio of integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
