# ADR 0202: Coherence confidence interval

Status: accepted, 2026-11-16. It goes with the coherence (ADR 0192) and the chi-squared
quantile of the PSD confidence interval (ADR 0201).

## Context

An estimated coherence from `K` segments scatters about the true value. Its exact sampling
distribution is awkward. The standard practical interval applies the Fisher transform to the
coherence magnitude `γ = √γ²`, treating `atanh γ` as normal with a standard deviation of
`1/√(2K − 2)`.

## Decision

- **The API.**
  - Python: `coherence_confidence_interval(coherence, num_segments, confidence=0.95)` in
    `spectral`.
  - C#: `Spectral.CoherenceConfidenceInterval(ReadOnlySpan<double> coherence, int numSegments,
    double confidence = 0.95)`.
  - Both return `CoherenceConfidenceInterval(lower, upper)`, two arrays of the input's length.
- **The definition.**
  - `s = z / √(2K − 2)`, where `z` is the standard normal quantile at `(1 + c)/2`.
  - `lower = max(0, tanh(atanh γ − s))²` and `upper = tanh(atanh γ + s)²`.
  - `γ² = 1` gives `[1, 1]`.
- **The normal quantile.** `z = √q₁(c)`, with `q₁` the private chi-squared quantile from
  ADR 0201 for one degree of freedom. This holds because `P(Z² ≤ z²) = c` for the two-sided
  `z`. No separate inverse-normal routine is added.
- **The rules.**
  - The coherence is one-dimensional, finite and in [0, 1].
  - `K` is an integer of at least 2.
  - `c` is strictly between 0 and 1.
  - Anything else is `invalid_argument`.
- **An approximation.** The interval is approximate. It is poor for small `K` and for small
  coherence, and the docs say so. As in ADR 0199, `K` counts independent segments. With
  overlap, the caller passes an effective count, for example `welch_dof(...)/2` rounded down.

## Consequences

- **Vectors.** Their expected values come from stdlib `statistics.NormalDist().inv_cdf`,
  `math.atanh` and `math.tanh`. They are independent of the chi-squared quantile, so they also
  check `q₁`. They cover the clip at 0, `γ² = 1` and the argument errors.
