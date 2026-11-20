# ADR 0429: The Ochiai coefficient

Status: accepted, 2026-11-19.

## Context

The Ochiai coefficient of two binary records is `TP / √(|A|·|B|)`: the cosine similarity of
the two records as 0/1 vectors, and the geometric mean of the recall and the precision
against a truth record. It sits between the F1 score (their harmonic mean) and the
Kulczynski coefficient (ADR 0428, their arithmetic mean).

## Decision

- **The API.**
  - Python: `ochiai_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.OchiaiCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP / √(|A|·|B|)`: the product of the counts is an exact integer, then one correctly
    rounded square root and one division, so both languages round alike.
  - From 0 to 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Either record with no 1 is an error: the denominator is zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly and takes the root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`: two roundings.
