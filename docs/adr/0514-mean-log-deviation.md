# ADR 0514: The mean log deviation

Status: accepted, 2026-11-20.

## Context

The mean log deviation (the Theil L index, the generalized entropy index at 0) is the mean
of `ln(μ/x)`: the log of the arithmetic mean less the log of the geometric mean. Like the
Theil index (ADR 0511) it splits exactly into a part within groups and a part between
them, and it weighs gaps at the bottom of the range more.

## Decision

- **The API.**
  - Python: `mean_log_deviation(samples)` in `measurements`, giving a float.
  - C#: `Measurements.MeanLogDeviation(ReadOnlySpan<double> samples)`.
- **The value.**
  - `L = (1/n)·Σ ln(μ/xᵢ)`, `μ` the mean, each term formed as the log of the ratio.
  - At least 0; 0 when every value is equal; no upper bound. Unchanged when every value
    is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value greater than
    0: a value of 0 makes the mean log deviation infinite.

## Consequences

- The cost is two passes.
- **Vectors.**
  - The generator takes the mean of dyadic values exactly in rationals and each
    logarithm in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
