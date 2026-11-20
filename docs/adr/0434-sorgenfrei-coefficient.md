# ADR 0434: The Sorgenfrei coefficient

Status: accepted, 2026-11-19.

## Context

The Sorgenfrei coefficient of two binary records is `TP² / (|A|·|B|)`: the product of the
shares of each record's 1s that the other also marks, so against a truth record the recall
times the precision. It is the square of the Ochiai coefficient (ADR 0429), given by name
because it is computed exactly from integers where the Ochiai coefficient needs a root.

## Decision

- **The API.**
  - Python: `sorgenfrei_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.SorgenfreiCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP²` and `|A|·|B|` exact integers, each converted to a double once (exact below
    `2⁵³`, which holds for any record shorter than `2²⁶` items), then one division.
  - From 0 to 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Either record with no 1 is an error: the denominator is zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
