# ADR 0411: The total variation distance

Status: accepted, 2026-11-19.

## Context

The total variation distance is the largest difference in probability that two distributions
can give the same event, and half their `L1` distance. It is the measure behind the best
possible test that tells two distributions apart from one draw, and the one the Hellinger
distance (ADR 0409) bounds from both sides.

## Decision

- **The API.**
  - Python: `total_variation_distance(p, q)` in `measurements`, giving a float.
  - C#: `Measurements.TotalVariationDistance(ReadOnlySpan<double> p, ReadOnlySpan<double> q)`.
  - Normalized as for the Kullback–Leibler divergence (ADR 0407): each by its own sum.
- **The value.**
  - `δ = ½·Σᵢ|Pᵢ − Qᵢ|`.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Per index, one subtraction and the absolute value; summed in
    order, halved, and clamped to at most 1.
  - Symmetric; a metric, from 0 to 1.
- **The rules.**
  - As for the Hellinger distance: equal lengths at least 1, finite, non-negative, each sum
    above zero, zeros anywhere.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms the distance exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
