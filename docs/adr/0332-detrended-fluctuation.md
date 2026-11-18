# ADR 0332: Detrended fluctuation analysis

Status: accepted, 2026-11-18.

## Context

Detrended fluctuation analysis (Peng et al., 1994) measures long-range correlation in a series
that may not be stationary. It integrates the series into a profile, removes a straight-line
fit in boxes of each size, and reads the scaling exponent `α` from how the remaining RMS grows
with the box size. White noise gives about 0.5, 1/f noise about 1 and Brownian motion about
1.5.

## Decision

- **The API.**
  - Python: `detrended_fluctuation(samples, scales)` in `measurements`, giving the frozen
    dataclass `DetrendedFluctuation(scales, fluctuations, alpha)` (`eq=False`, as it holds
    arrays).
  - C#: `Measurements.DetrendedFluctuation(ReadOnlySpan<double> samples,
    ReadOnlySpan<int> scales)`, giving the record `DetrendedFluctuation(int[] Scales,
    double[] Fluctuations, double Alpha)`.
- **The value.** This is DFA-1, the first-order version: a straight line is removed in each
  box. With `N` samples, 0-based:
  - The profile is `Y[i] = Σ_{j=0}^{i} (x[j] − x̄)`, of length `N`.
  - For scale `s`, the profile is cut into `B = floor(N/s)` boxes from the start; the samples
    left at the end are not used.
  - In each box, `t = 0 … s−1` and a least-squares line `a + b·t` is fitted to the box's
    `Y`. Its residuals are `r_t`.
  - `F(s) = sqrt(Σ_boxes Σ_t r_t² / (B·s))`.
  - `α` is the least-squares slope of `ln F(s)` against `ln s`.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `scales` integers, at least two of them, strictly increasing, each with `4 ≤ s ≤ N`.
  - Every `F(s)` must be above 0, so a constant, or a series whose profile is a straight
    line in every box, is rejected.

## Consequences

- **Vectors.**
  - The samples are dyadic. The generator computes the profile, each box's fit and each
    `F(s)²` exactly in rationals. It then takes the square roots, the logarithms and the
    slope in float.
  - The tolerance is `abs 1e-12, rel 1e-11`. The two languages sum the mean in a different
    order.
