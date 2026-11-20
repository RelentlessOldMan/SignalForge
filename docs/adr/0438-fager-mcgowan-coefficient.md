# ADR 0438: The Fager-McGowan coefficient

Status: accepted, 2026-11-19.

## Context

The Fager-McGowan coefficient of two binary records is
`TP / √(|A|·|B|) − 1 / (2·√max(|A|, |B|))`: the Ochiai coefficient (ADR 0429) less a
correction that shrinks as the larger record's count of 1 grows, so that small samples are
not credited with chance overlap. It runs from `−1/2` (no shared 1 and single 1s) up to
just below 1.

## Decision

- **The API.**
  - Python: `fager_mcgowan_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.FagerMcGowanCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP / √(|A|·|B|)` as for the Ochiai coefficient, then `1 / (2·√m)` with `m` the larger
    count, rooted once, then the difference: the same operations in the same order in both
    languages.
  - Below 1. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Either record with no 1 is an error, as for the Ochiai coefficient.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly and takes the roots in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`: the difference can cancel.
