# ADR 0404: The energy distance between two samples

Status: accepted, 2026-11-19.

## Context

Székely and Rizzo's energy distance compares two samples through mean absolute
differences: twice the mean distance between the samples, less the mean distance within each.
For one-dimensional data it is twice the integral of `(F_x − F_y)²`, so it weighs every gap
between the distribution functions where Kolmogorov–Smirnov (ADR 0402) takes only the
largest.

## Decision

- **The API.**
  - Python: `energy_distance(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.EnergyDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - `E = 2A − B − C`: `A = Σᵢⱼ|xᵢ − yⱼ|/(n_x·n_y)`, `B = Σᵢₖ|xᵢ − xₖ|/n_x²`,
    `C = Σⱼₗ|yⱼ − yₗ|/n_y²`, every ordered pair, equal indices included.
  - This is Székely and Rizzo's squared form, in the units of the data. The square root, which
    some libraries return under the same name, is not taken.
  - Each sum is a double loop in order, outer index first, in `double`. A result below zero
    from rounding is returned as 0, since `E ≥ 0`.
  - Symmetric; zero when both samples hold the same values in the same proportions.
- **The rules.**
  - Each sample one-dimensional, real and finite, at least 1.

## Consequences

- The cost is `(n_x + n_y)²` absolute differences; no sort.
- **Vectors.**
  - The generator forms all three sums exactly in rationals.
  - The tolerance is `abs 1e-13, rel 1e-12`: the three sums cancel, so the error is set by
    their size, not by `E`'s.
