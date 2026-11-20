# ADR 0435: The Forbes coefficient

Status: accepted, 2026-11-19.

## Context

The Forbes coefficient of two binary records is `n·TP / (|A|·|B|)`: the number of items
both mark 1 over the number expected if the two records were independent with the same
counts of 1, `|A|·|B| / n`. It is 1 for no association, above 1 when the 1s gather together,
and at most `n / max(|A|, |B|)`.

## Decision

- **The API.**
  - Python: `forbes_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.ForbesCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `n·TP` and `|A|·|B|` exact integers, each converted to a double once (exact below
    `2⁵³`, which holds for any record shorter than `2²⁶` items), then one division.
  - From 0 up; not bounded by 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Either record with no 1 is an error: the denominator is zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
