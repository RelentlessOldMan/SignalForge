# ADR 0468: The second Baroni-Urbani-Buser coefficient

Status: accepted, 2026-11-20.

## Context

The second Baroni-Urbani-Buser coefficient of two binary records is
`(r + TP − FN − FP) / (r + TP + FN + FP)` with `r = sqrt(TP·TN)`: the first coefficient
(ADR 0433) stretched from 0..1 to −1..1, so that it equals twice the first minus 1. 1 when
the records agree everywhere, −1 when they disagree everywhere.

## Decision

- **The API.**
  - Python: `baroni_urbani_buser_ii(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.BaroniUrbaniBuserII(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `r` is the exact integer `TP·TN` converted to a double once and rooted once, as for
    the first coefficient. The exact integers `TP − FN − FP` and `TP + FN + FP` are each
    converted to a double once and added to `r`; then one division.
  - From −1 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Both records all 0 is an error: the denominator is then 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, takes `sqrt(TP·TN)` correctly rounded in
    40-digit decimals and forms the value there.
  - The tolerance is `abs 1e-15, rel 1e-14`.
