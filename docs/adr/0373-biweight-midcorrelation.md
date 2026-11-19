# ADR 0373: Biweight midcorrelation

Status: accepted, 2026-11-18.

## Context

The biweight midcorrelation (Wilcox; used widely as `bicor`) is a robust stand-in for
Pearson's r (ADR 0371). Samples far from the median get little or no weight, so a few
outliers cannot drive it.

## Decision

- **The API.**
  - Python: `biweight_midcorrelation(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.BiweightMidcorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.** For each record:
  - The median `m` is the middle sorted value, or `(a + b)/2` of the two middle values for
    an even count.
  - `MAD` is the median, by the same rule, of `|x − m|`, unscaled.
  - `u = (x − m)/(9 · MAD)`, the product `9 · MAD` formed first.
  - The weight is `w = (1 − u·u)·(1 − u·u)` where `|u| < 1`, and 0 elsewhere.
  - `a = (x − m) · w`.
  - With `b` built the same way from `y`, `bicor = Σ a b/√(Σ a² · Σ b²)`. The product is
    formed first, then the square root, then the quotient.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - `N ≥ 2`.
  - Neither `MAD` may be 0. That happens when half or more of a record's samples are equal.
    Some libraries fall back to Pearson's r in that case. SignalForge refuses instead, so
    the result is always the same statistic.
  - If `MAD > 0`, some sample with `0 < |x − m| ≤ 2 MAD` has a positive weight, so `Σ a² > 0`.

## Consequences

- **Vectors.**
  - The vector samples are dyadic, so the medians and `MAD` are exact.
  - The generator takes `u`, `w`, `a` and the sums exactly in rationals, then the square root
    and the quotient in float. It asserts that no `|u|` is within `10⁻⁹` of 1.
  - The tolerance is `abs 1e-14, rel 1e-13`.
