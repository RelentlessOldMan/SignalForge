# ADR 0424: The simple matching coefficient

Status: accepted, 2026-11-19.

## Context

The simple matching coefficient of two binary records is the share of items on which they
agree, a 1 in both or a 0 in both. Unlike the Jaccard index (ADR 0388), it counts shared
absences, which matters when 0 is as meaningful as 1: the bits of a sent and a received
word, where it is one minus the bit error ratio.

## Decision

- **The API.**
  - Python: `simple_matching_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.SimpleMatchingCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `(TP + TN) / n`, with `n` the length; integer counts and one division.
  - From 0 to 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other error: the length is never zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts agreements directly; the value is a ratio of integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
