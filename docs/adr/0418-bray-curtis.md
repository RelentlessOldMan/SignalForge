# ADR 0418: The Bray–Curtis dissimilarity

Status: accepted, 2026-11-19.

## Context

The Bray–Curtis dissimilarity compares two vectors of non-negative amounts, such as counts
or band powers, by the share of their combined total that does not match. Unlike the
distribution measures (ADRs 0407–0416) it does not normalize each vector to sum to one, so a
difference in total amount counts too; unlike the Canberra distance (ADR 0417) it weights
each coordinate by its size.

## Decision

- **The API.**
  - Python: `bray_curtis(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.BrayCurtis(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - `BC(x, y) = Σᵢ |xᵢ − yᵢ| / Σᵢ (xᵢ + yᵢ)`.
  - Both sums are taken in order in one pass, the second as `xᵢ + yᵢ` per index; the
    quotient is clamped to at most 1.
  - Symmetric; from 0 (equal) to 1 (no index where both are positive). Not a metric.
- **The rules.**
  - `x` and `y` are finite and non-negative, of equal length at least 1.
  - The denominator must be above zero: both all zero is an error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator forms the value exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
