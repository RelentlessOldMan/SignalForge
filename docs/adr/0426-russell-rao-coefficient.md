# ADR 0426: The Russell-Rao coefficient

Status: accepted, 2026-11-19.

## Context

The Russell-Rao coefficient of two binary records is the share of all items that both mark
1: `TP / n`. It ignores shared absences in the numerator but keeps them in the denominator,
so it is the joint presence rate, as in how often two detectors fire together per frame.
It is at most the simple matching coefficient (ADR 0424) and at most the Jaccard index
(ADR 0388).

## Decision

- **The API.**
  - Python: `russell_rao_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.RussellRaoCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP / n` from integer counts, one division.
  - From 0 to 1; 1 only when both records are all 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other error: the length is never zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the shared 1s directly; the value is a ratio of integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
