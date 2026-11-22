# ADR 0539: The McIntosh dominance

Status: accepted, 2026-11-21.

## Context

McIntosh (1967) measures diversity by the Euclidean length `U = √(Σ xᵢ²)` of the record
taken as a vector of counts, and scales it as `D = (N − U)/(N − √N)`, `N` the total.
Unlike the share-based measures it depends on the scale of the values: doubling every
value changes it.

## Decision

- **The API.**
  - Python: `mcintosh_dominance(samples)` in `measurements`, giving a float.
  - C#: `Measurements.McIntoshDominance(ReadOnlySpan<double> samples)`.
- **The value.**
  - `D = (N − U)/(N − √N)`, `N = Σᵢ xᵢ` and `Σᵢ xᵢ²` added in record order, `U` its square
    root.
  - At least 0, and 0 when one value holds the total. For whole-number counts it is at most
    1, as `Σ xᵢ² ≥ N`; for other values it can exceed 1 when `N < n`.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    with `N > 1` so the denominator is positive (otherwise `invalid_argument`).

## Consequences

- One pass for the total, one for the squares; no sort.
- **Vectors.**
  - The generator forms the sums exactly and the square roots in 50-digit `decimal`.
  - The tolerance is `abs 1e-14, rel 1e-13`: `N − U` loses digits when one value is close
    to the total.
