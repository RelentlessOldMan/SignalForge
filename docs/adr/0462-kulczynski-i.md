# ADR 0462: The first Kulczynski coefficient

Status: accepted, 2026-11-20.

## Context

Kulczynski's first coefficient for two binary records is `TP / (FN + FP)`: the shared 1s
per mismatching item, the Jaccard index recast as odds. Shared 0s do not count. 0 when no 1
is shared; it has no upper end and is undefined when the records agree everywhere. His
second coefficient is ADR 0428.

## Decision

- **The API.**
  - Python: `kulczynski_i(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.KulczynskiI(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Numerator and denominator exact integers, each converted to a double once, then one
    division.
  - At least 0. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `FN + FP = 0` is an error: the records agree everywhere.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
