# ADR 0399: Glass's delta

Status: accepted, 2026-11-19.

## Context

When a treatment changes the spread as well as the mean, pooling the two variances as Cohen's
d (ADR 0397) does mixes the effect into the yardstick. Glass (1976) measured the difference in
units of the control group's standard deviation alone.

## Decision

- **The API.**
  - Python: `glass_delta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.GlassDelta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - `x` is the treated sample and `y` the control; positive when `x` has the larger mean.
- **The value.**
  - `Δ = (x̄ − ȳ)/s_y`, `s_y² = Σ(yⱼ − ȳ)²/(n_y − 1)`.
  - Each mean is its sum in order over its count; the squared deviations of `y` are summed in
    order from `ȳ`; then the root and one division.
  - Not symmetric: swapping the samples changes the yardstick, not just the sign.
- **The rules.**
  - Both samples one-dimensional, real and finite. `x` at least 1, `y` at least 2.
  - `s_y > 0`.

## Consequences

- The cost is one pass over `x` and two over `y`.
- **Vectors.**
  - The generator forms the means and the sum of squares exactly in rationals and the root in
    40-digit decimal.
  - The tolerance is `abs 1e-15, rel 1e-13`.
