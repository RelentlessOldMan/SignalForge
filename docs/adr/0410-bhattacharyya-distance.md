# ADR 0410: The Bhattacharyya distance

Status: accepted, 2026-11-19.

## Context

The Bhattacharyya coefficient `Σ√(PᵢQᵢ)` measures the overlap of two distributions. Its
negative logarithm, the Bhattacharyya distance, bounds the error of telling the two apart
from one draw and adds over independent features, which the Hellinger distance (ADR 0409)
does not.

## Decision

- **The API.**
  - Python: `bhattacharyya_distance(p, q)` in `measurements`, giving a float.
  - C#: `Measurements.BhattacharyyaDistance(ReadOnlySpan<double> p, ReadOnlySpan<double> q)`.
  - Normalized as for the Kullback–Leibler divergence (ADR 0407): each by its own sum.
- **The value.**
  - `D_B = −ln BC`, `BC = Σᵢ √(Pᵢ·Qᵢ)`.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Per index, one product and one root; the roots are summed
    in order. `BC` is clamped to at most 1, then `0 − ln BC` (so equal distributions give
    `+0`).
  - Symmetric. Not a metric: the triangle inequality fails.
- **The rules.**
  - As for the Hellinger distance: equal lengths at least 1, finite, non-negative, each sum
    above zero, zeros anywhere.
  - `BC = 0`, no index where both are positive, is an error: the distance is infinite.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms the distributions exactly in rationals, the roots and the logarithm
    in 40-digit decimal.
  - The tolerance is `abs 1e-15, rel 1e-13`.
