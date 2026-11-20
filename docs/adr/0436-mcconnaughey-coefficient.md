# ADR 0436: The McConnaughey coefficient

Status: accepted, 2026-11-19.

## Context

The McConnaughey coefficient of two binary records is `(TP² − FN·FP) / (|A|·|B|)`. It is
the Kulczynski coefficient (ADR 0428) moved onto `[−1, 1]`, `2·K − 1`: against a truth
record, recall plus precision less one. 1 for identical records, −1 when they share no 1.

## Decision

- **The API.**
  - Python: `mcconnaughey_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.McConnaugheyCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP² − FN·FP` and `|A|·|B|` exact integers, each converted to a double once (exact
    below `2⁵³`, which holds for any record shorter than `2²⁶` items), then one division.
  - From −1 to 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Either record with no 1 is an error: the denominator is zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
