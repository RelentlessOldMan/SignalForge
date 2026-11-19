# ADR 0349: Correlation sum

Status: accepted, 2026-11-18.

## Context

The correlation sum of Grassberger and Procaccia (1983) is the share of pairs of embedded
vectors closer than a radius `r`. For an attractor, `C(r)` grows as `r^D` over a range of
radii, and `D` is the correlation dimension. Like the box and Higuchi dimensions (ADR 0330),
the slope only means something over the scaling range, so the caller picks the radii and
gets every `C(r)` back as well as the slope.

## Decision

- **The API.**
  - Python: `correlation_sum(samples, m, radii, delay=1, theiler=0)` in `measurements`,
    giving a frozen dataclass `CorrelationSum(radii, values, dimension)`.
  - C#: `Measurements.CorrelationSum(ReadOnlySpan<double> samples, int m,
    ReadOnlySpan<double> radii, int delay = 1, int theiler = 0)`, giving the record
    `CorrelationSum(double[] Radii, double[] Values, double Dimension)`.
- **The value.**
  - The vectors are `v_i = (x_i, x_{i+τ}, …, x_{i+(m−1)τ})` for `i = 0 … W − 1`, with
    `W = N − (m − 1)τ`.
  - The pairs are `i < j` with `j − i > w`, the Theiler window. There are `P` of them.
  - `C(r)` is the number of those pairs whose Chebyshev distance is **strictly** below `r`,
    over `P`.
  - `dimension` is the least-squares slope of `ln C(r)` against `ln r`.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `m`, `delay` integers of at least 1, and `theiler` an integer of at least 0.
  - There must be at least one pair.
  - There must be at least two radii, finite, positive and strictly increasing.
  - Every `C(r)` must be above 0, or the slope is undefined; a radius below every distance
    is an error.

## Consequences

- **Vectors.**
  - The samples and radii are dyadic, so every distance is exact in float and the strict
    comparison is exact. The generator counts in rationals. The slope is taken in float.
  - The cases include a distance exactly equal to a radius, which must not count.
  - The tolerance is `abs 1e-12, rel 1e-12`.
