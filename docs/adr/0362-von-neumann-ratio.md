# ADR 0362: von Neumann ratio

Status: accepted, 2026-11-18.

## Context

Von Neumann (1941) proposed a test of serial correlation: the mean square successive
difference divided by the variance. It is about 2 for an i.i.d. record, below 2 for positive
correlation and above 2 for negative. Its form about the mean is the Durbin–Watson statistic,
the usual check on regression residuals. It also underlies the Bartels rank test.

## Decision

- **The API.**
  - Python: `von_neumann_ratio(samples)` in `measurements`, giving a float.
  - C#: `Measurements.VonNeumannRatio(ReadOnlySpan<double> samples)`.
- **The value.**
  - `Σ_{t=0}^{N−2} (x_{t+1} − x_t)² / Σ_{t=0}^{N−1} (x_t − x̄)²`.
  - This is the plain ratio of the two sums. Von Neumann's own `δ²/s²` divides them by
    `N − 1` and `N`, which scales it by `N/(N − 1)`. Both forms appear in the literature, and
    SignalForge uses the plain one.
  - For an i.i.d. record, the numerator and denominator have expectations `2(N − 1)σ²` and
    `(N − 1)σ²`, so the ratio is about 2.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `N ≥ 2`, and not every sample equal.

## Consequences

- **Vectors.**
  - The samples are dyadic, so the generator takes the value exactly in rationals.
  - The tolerance is `abs 1e-14, rel 1e-13`.
