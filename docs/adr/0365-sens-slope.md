# ADR 0365: Sen's slope

Status: accepted, 2026-11-18.

## Context

Sen (1968), building on Theil (1950), estimates a linear trend by the median of all pairwise
slopes. It is robust to outliers, and it is the usual partner of the Mann–Kendall test
(ADR 0364): Mann–Kendall says whether there is a trend, and Sen's slope says how large it is.

## Decision

- **The API.**
  - Python: `sens_slope(samples)` in `measurements`, giving a float.
  - C#: `Measurements.SensSlope(ReadOnlySpan<double> samples)`.
- **The value.**
  - The slopes are `(x_j − x_i)/(j − i)` for every `i < j`, computed in that form. The unit
    is per sample.
  - The value is their median. With an even number of slopes it is `(a + b)/2`, where `a`
    and `b` are the two middle ones.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `N ≥ 2`.

## Consequences

- **Vectors.**
  - The samples are dyadic, so the generator takes every slope and the median exactly in
    rationals.
  - The tolerance is `abs 1e-14, rel 1e-13`.
