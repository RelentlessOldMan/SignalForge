# ADR 0397: Cohen's d

Status: accepted, 2026-11-19.

## Context

Cohen (1988) measured the size of a difference between two group means in units of their
common spread, so that effects on different scales can be compared. It is the standard
effect size beside a two-sample t test.

## Decision

- **The API.**
  - Python: `cohen_d(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.CohenD(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - Positive when `x` has the larger mean.
- **The value.**
  - `d = (x̄ − ȳ)/s`, `s² = (Σ(xᵢ − x̄)² + Σ(yⱼ − ȳ)²)/(n_x + n_y − 2)`: the pooled
    standard deviation, not the one of Glass or the root mean of the two variances.
  - Each mean is its sum in order over its count; the squared deviations are summed in
    order from those means. Then `s` is the root of the pooled variance and one division
    gives `d`.
- **The rules.**
  - Both samples one-dimensional, real and finite, each at least 2.
  - `s > 0`: not every value equal to its own sample's mean.

## Consequences

- The cost is two passes over each sample.
- **Vectors.**
  - The generator forms the means and the sums of squares exactly in rationals and takes the
    root in 40-digit decimal.
  - The tolerance is `abs 1e-15, rel 1e-13`, for sums in order against the exact ones.
