# ADR 0440: The Braun-Blanquet coefficient

Status: accepted, 2026-11-19.

## Context

The Braun-Blanquet coefficient of two binary records is `TP / max(|A|, |B|)`: the shared
1s over the larger count of 1. It is the counterpart of the overlap coefficient, which
divides by the smaller count, and is never above the Ochiai coefficient. From 0 to 1.

## Decision

- **The API.**
  - Python: `braun_blanquet_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.BraunBlanquetCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The two integer counts converted to doubles, then one correctly rounded division.
  - From 0 to 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Both records with no 1 is an error: the denominator is zero. One record with no 1
    gives 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly and divides in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
