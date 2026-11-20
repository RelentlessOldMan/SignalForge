# ADR 0425: The Rogers-Tanimoto coefficient

Status: accepted, 2026-11-19.

## Context

The Rogers-Tanimoto coefficient of two binary records weighs disagreements double:
`(TP + TN) / (TP + TN + 2·(FN + FP))`. With `m` the agreements and `u` the disagreements
it is `m / (m + 2u)`, never above the simple matching coefficient (ADR 0424), `m / (m + u)`,
and equal to it only at 0 and 1. It suits records where a mismatch should cost more than a
match earns.

## Decision

- **The API.**
  - Python: `rogers_tanimoto_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.RogersTanimotoCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `m / (m + 2u)` from integer counts, the denominator an integer, then one division.
  - From 0 to 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other error: `m + 2u` is at least the length.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts agreements directly; the value is a ratio of integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
