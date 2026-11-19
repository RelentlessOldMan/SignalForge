# ADR 0402: The two-sample Kolmogorov–Smirnov statistic

Status: accepted, 2026-11-19.

## Context

The Vargha–Delaney A (ADR 0401) and Cliff's delta (ADR 0400) ask whether one sample tends to
be larger. Two samples can share a median and still differ in spread or shape. The
Kolmogorov–Smirnov statistic is the largest gap between their empirical distribution
functions, which is zero only when the two samples hold the same values in the same
proportions.

## Decision

- **The API.**
  - Python: `kolmogorov_smirnov(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.KolmogorovSmirnov(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - The statistic only; no p-value.
- **The value.**
  - `D = max over t of |F_x(t) − F_y(t)|`, `F_x(t) = #(xᵢ ≤ t)/n_x`. The maximum is reached
    at a sample value, so only those are checked.
  - At each distinct value `t` of the pooled samples, the whole number
    `|#(xᵢ ≤ t)·n_y − #(yⱼ ≤ t)·n_x|` is formed; the largest is converted to `double` and
    divided once by `n_x·n_y`. The result is the correctly rounded rational.
  - Symmetric in the two samples; from 0 to 1.
- **The rules.**
  - Each sample one-dimensional, real and finite, at least 1.

## Consequences

- The cost is a sort of each sample and a merge.
- **Vectors.**
  - The generator checks every pooled value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
