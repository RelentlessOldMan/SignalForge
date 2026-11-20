# ADR 0461: The third Sokal-Sneath coefficient

Status: accepted, 2026-11-20.

## Context

The third of Sokal and Sneath's coefficients for two binary records is
`(TP + TN) / (FN + FP)`: the matching items per mismatching item, simple matching recast as
odds. 0 when the records disagree everywhere; it has no upper end and is undefined when
they agree everywhere. The fourth and fifth coefficients of the series are ADR 0459 and
ADR 0460.

## Decision

- **The API.**
  - Python: `sokal_sneath_iii(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.SokalSneathIII(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Numerator and denominator exact integers, each converted to a double once, then one
    division.
  - At least 0. Symmetric in the two records; unchanged when either or both records are
    flipped together.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `FN + FP = 0` is an error: the records agree everywhere.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
