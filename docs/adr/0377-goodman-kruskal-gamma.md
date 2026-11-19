# ADR 0377: Goodman and Kruskal's gamma

Status: accepted, 2026-11-19.

## Context

Goodman and Kruskal (1954) measured the association of two ordered records by the pairs of
samples they agree and disagree on, leaving out the pairs either record cannot order. With
many ties (coarse levels, quantized data) it stays at ±1 for a monotone pair where Kendall's
tau-b (ADR 0370) does not.

## Decision

- **The API.**
  - Python: `goodman_kruskal_gamma(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.GoodmanKruskalGamma(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - Over all pairs `i < j`, `C` counts those with `(x_i − x_j)(y_i − y_j) > 0` and `D` those
    with `< 0`, decided by comparison, not by forming the differences. Pairs tied in `x` or `y`
    count in neither.
  - `γ = (C − D)/(C + D)`, from −1 to 1.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - At least one pair untied in both (`C + D > 0`, so `N ≥ 2`).

## Consequences

- The direct count is `O(N²)`.
- **Vectors.**
  - The generator counts the pairs by brute force; the value is a ratio of two counts.
  - The tolerance is `abs 1e-15, rel 1e-15`.
