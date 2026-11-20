# ADR 0456: Faith's coefficient

Status: accepted, 2026-11-20.

## Context

Faith's coefficient of two binary records is `(TP + TN/2) / n`: the share of items both
mark 1, with the items both mark 0 counted as half an agreement. Shared 1s weigh more than
shared 0s, so unlike simple matching it changes when both records are flipped. 1 when both
records are all 1, 0 when they disagree everywhere.

## Decision

- **The API.**
  - Python: `faith_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.FaithCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - As `(2·TP + TN) / (2·n)`: numerator and denominator exact integers, each converted to a
    double once, then one division.
  - From 0 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other error: the denominator is at least 2.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals as written,
    with the half kept as a fraction.
  - The tolerance is `abs 1e-15, rel 1e-15`.
