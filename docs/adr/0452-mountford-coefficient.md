# ADR 0452: Mountford's coefficient

Status: accepted, 2026-11-19.

## Context

Mountford's coefficient of two binary records is `2·TP / (TP·FN + TP·FP + 2·FN·FP)`, a
similarity of two species lists that weighs the shared 1s against the products of the
counts unique to each. `TN` plays no part. It is 0 when no 1 is shared and has no fixed
upper end; it grows without bound as the records come to agree, and is undefined when they
agree everywhere (`FN = FP = 0`).

## Decision

- **The API.**
  - Python: `mountford_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.MountfordCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Numerator and denominator exact integers, each converted to a double once, then one
    division.
  - At least 0. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A zero denominator is an error: that is `FN = FP = 0` (the 1s agree everywhere), or
    `TP = 0` with `FN·FP = 0`.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
