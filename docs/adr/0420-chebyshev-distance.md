# ADR 0420: The Chebyshev distance

Status: accepted, 2026-11-19.

## Context

The Chebyshev distance is the largest coordinate difference of two vectors: the limit of the
Minkowski distance (ADR 0419) as its order grows, which that function does not take. It is
the measure behind a peak error bound, as in a waveform's worst sample against a reference.

## Decision

- **The API.**
  - Python: `chebyshev_distance(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.ChebyshevDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - `d(x, y) = maxᵢ |xᵢ − yᵢ|`.
  - One pass; each difference is one rounded subtraction, so the result is the correctly
    rounded largest difference, the same in both languages.
  - Symmetric, a metric.
- **The rules.**
  - As for the Minkowski distance: `x` and `y` real and finite, of equal length at least 1;
    a difference beyond the largest double is an error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator forms the differences exactly in rationals.
  - The tolerance is `abs 0, rel 1e-15`: the result is exact.
