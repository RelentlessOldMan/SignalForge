# ADR 0467: The Rogot-Goldberg coefficient

Status: accepted, 2026-11-20.

## Context

The Rogot-Goldberg coefficient of two binary records is
`TP/(2·TP + FN + FP) + TN/(2·TN + FN + FP)`: the mean of the Dice coefficient of the 1s
and the Dice coefficient of the 0s, so it treats the two values alike. 1 when the records
agree everywhere, 0 when they disagree everywhere.

## Decision

- **The API.**
  - Python: `rogot_goldberg_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.RogotGoldbergCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Each of the two quotients has an exact integer numerator and denominator, each
    converted to a double once; the two quotients are added in that order.
  - From 0 to 1. Symmetric in the two records; unchanged when both records are flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A denominator of 0 is an error: `2·TP + FN + FP = 0` when both records are all 0, and
    `2·TN + FN + FP = 0` when both are all 1.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
