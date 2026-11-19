# ADR 0403: The first Wasserstein distance between two samples

Status: accepted, 2026-11-19.

## Context

The Kolmogorov–Smirnov statistic (ADR 0402) is the largest gap between two empirical
distribution functions and ignores how far apart the values are. The first Wasserstein
(earth mover's) distance is the area between them: the least average distance values must
move to turn one sample into the other, in the units of the data.

## Decision

- **The API.**
  - Python: `wasserstein_distance(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.WassersteinDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - `W = ∫|F_x(t) − F_y(t)| dt`, each sample weighted equally over its values.
  - With `t₀ < t₁ < … < t_k` the distinct pooled values, `F_x − F_y` is constant on each
    `[t_m, t_{m+1})`. The whole number `g_m = |#(x ≤ t_m)·n_y − #(y ≤ t_m)·n_x|` is formed;
    `Σ g_m·(t_{m+1} − t_m)` is summed in order of `m` in `double`, then divided once by
    `n_x·n_y`.
  - Symmetric; zero when both samples hold the same values in the same proportions; in the
    units of the samples.
- **The rules.**
  - Each sample one-dimensional, real and finite, at least 1.

## Consequences

- The cost is a sort of each sample and a merge.
- **Vectors.**
  - The generator sums the same intervals exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-13`: the widths and the products round.
