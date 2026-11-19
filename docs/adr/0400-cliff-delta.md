# ADR 0400: Cliff's delta

Status: accepted, 2026-11-19.

## Context

Cliff (1993) proposed an effect size for ordinal data that needs no means or spreads: over
every pair of one value from each sample, how much more often the first sample is larger
than smaller. It is unchanged by any increasing map of the data.

## Decision

- **The API.**
  - Python: `cliff_delta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.CliffDelta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - Positive when `x` tends to be larger.
- **The value.**
  - `δ = (#(xᵢ > yⱼ) − #(xᵢ < yⱼ))/(n_x·n_y)` over all `n_x·n_y` pairs; ties count in
    neither. From −1 to 1.
  - Both counts are whole numbers, found by sorting `y` and searching it for each `xᵢ`. Their
    difference and the product are converted to `double`, then one division.
  - Antisymmetric: swapping the samples negates it.
- **The rules.**
  - Both samples one-dimensional, real and finite, each at least 1.

## Consequences

- The cost is a sort of `y` and a binary search per `xᵢ`.
- **Vectors.**
  - The generator compares every pair.
  - The tolerance is `abs 1e-15, rel 1e-15`.
