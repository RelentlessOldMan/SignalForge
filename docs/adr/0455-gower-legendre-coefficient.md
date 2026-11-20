# ADR 0455: The Gower-Legendre coefficient

Status: accepted, 2026-11-20.

## Context

The Gower-Legendre coefficient of two binary records is
`(TP + TN) / (TP + TN + (FN + FP)/2)`: the share of matching items, with each mismatch
weighted by half. It sits above simple matching and below 1; 1 when the records agree
everywhere, 0 when they disagree everywhere.

## Decision

- **The API.**
  - Python: `gower_legendre_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.GowerLegendreCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - As `2·(TP + TN) / (2·(TP + TN) + FN + FP)`: numerator and denominator exact integers,
    each converted to a double once, then one division.
  - From 0 to 1. Symmetric in the two records; unchanged when both records are flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other error: the denominator is at least `n`.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals as written,
    with the half kept as a fraction.
  - The tolerance is `abs 1e-15, rel 1e-15`.
