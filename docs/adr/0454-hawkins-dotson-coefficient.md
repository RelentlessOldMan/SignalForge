# ADR 0454: The Hawkins-Dotson coefficient

Status: accepted, 2026-11-20.

## Context

The Hawkins-Dotson coefficient of two binary records is the mean of
`TP / (TP + FN + FP)`, the Jaccard index of the 1s, and `TN / (TN + FN + FP)`, the same for
the 0s. Unlike the Jaccard index it counts shared 0s as agreement too, each kind on its own
scale. 1 when the records agree everywhere, 0 when they disagree everywhere.

## Decision

- **The API.**
  - Python: `hawkins_dotson_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.HawkinsDotsonCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - With `m = FN + FP`, as one fraction
    `(TP·(TN + m) + TN·(TP + m)) / (2·(TP + m)·(TN + m))`: numerator and denominator exact
    integers, each converted to a double once, then one division.
  - From 0 to 1. Symmetric in the two records; unchanged when both records are flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A zero denominator is an error: `TP + m = 0` (both records all 0) or `TN + m = 0`
    (both all 1).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the two Jaccard indices in rationals,
    then their mean.
  - The tolerance is `abs 1e-15, rel 1e-15`.
