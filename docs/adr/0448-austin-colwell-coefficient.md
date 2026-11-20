# ADR 0448: The Austin-Colwell coefficient

Status: accepted, 2026-11-19.

## Context

The Austin-Colwell coefficient of two binary records is `(2/π)·asin(√p)` with
`p = (TP + TN)/n`, the simple matching coefficient, put through the arcsine square-root
transform that steadies the variance of a proportion. 1 when the records agree everywhere,
0 when they disagree everywhere, 1/2 when they agree on half the items.

## Decision

- **The API.**
  - Python: `austin_colwell_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.AustinColwellCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `p` is `TP + TN` over `n`, both exact integers converted to doubles once, then one
    division. The value is `asin(√p) · 2 / π`, in that order, from the platform's `asin`;
    `asin` is not correctly rounded, so the two languages may differ in the last bits.
  - From 0 to 1. Symmetric in the two records; flipping one record gives
    `1 − value` in exact arithmetic.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No further error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and finds the arcsine in 40-digit decimals by
    its arctangent `atan(√(p/(1 − p)))`, the series after halving, pi from Machin's formula.
  - The tolerance is `abs 1e-15, rel 1e-14`.
