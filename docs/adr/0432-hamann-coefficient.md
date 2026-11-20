# ADR 0432: The Hamann coefficient

Status: accepted, 2026-11-19.

## Context

The Hamann coefficient of two binary records is the share of items they agree on minus the
share they disagree on: `((TP + TN) − (FN + FP)) / n`. It is the simple matching
coefficient (ADR 0424) moved onto `[−1, 1]`, `2·SMC − 1`: 1 for identical records, −1 for
complementary ones, 0 when half the items agree.

## Decision

- **The API.**
  - Python: `hamann_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.HamannCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `(m − u) / n` with `m` the agreements and `u` the disagreements: an exact integer over
    the length, one division.
  - From −1 to 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
    Nothing else can fail.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the agreements directly; the value is a ratio of integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
