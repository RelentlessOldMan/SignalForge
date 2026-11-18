# ADR 0330: Higuchi fractal dimension

Status: accepted, 2026-11-18.

## Context

Higuchi's method (1988) estimates the fractal dimension of a time series from how its curve
length grows as it is sampled more finely. It works straight on the samples, needs no phase
space, and is a common feature for EEG and other irregular series. A smooth curve gives 1,
white noise close to 2 and Brownian motion close to 1.5.

## Decision

- **The API.**
  - Python: `higuchi_dimension(samples, k_max)` in `measurements`, giving a float.
  - C#: `Measurements.HiguchiDimension(ReadOnlySpan<double> samples, int kMax)`.
- **The value.** With `N` samples, 0-based:
  - For each `k = 1 … k_max` and each start `m = 0 … k−1`, `n_m = floor((N − 1 − m)/k)`
    steps.
  - `L_m(k) = (Σ_{i=1}^{n_m} |x[m + i·k] − x[m + (i−1)·k]|) · (N − 1) / (n_m·k) / k`. The
    factor `(N − 1)/(n_m·k)` scales each length to the whole record.
  - `L(k)` is the mean of the `L_m(k)` over the `k` starts.
  - `X_k = ln(1/k) = −ln k` and `Y_k = ln L(k)`. The dimension is the least-squares slope
    `Σ (X − X̄)(Y − Ȳ) / Σ (X − X̄)²`.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `k_max` an integer of at least 2, with `2·k_max ≤ N` so that every start has a step.
  - Every `L(k)` must be above 0. A constant signal has no length, so it is rejected.

## Consequences

- **Vectors.**
  - The samples are dyadic. The generator computes each `L(k)` exactly in rationals and takes
    the logarithms and the fit in float.
  - A straight line gives `L(k) = (N − 1)/k` and a dimension of 1, which the generator
    asserts.
  - The tolerance is `abs 1e-12, rel 1e-12`.
