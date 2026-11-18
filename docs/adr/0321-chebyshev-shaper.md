# ADR 0321: Chebyshev waveshaper

Status: accepted, 2026-11-18.

## Context

The Chebyshev polynomials have the property `T_k(cos θ) = cos(k·θ)`. A waveshaper
`y = Σ_k w_k·T_k(x)` therefore turns a full-scale cosine into exactly the harmonic mix
`Σ_k w_k·cos(k·θ)`. That makes it the standard way to design a distortion with a chosen
spectrum (Le Brun, 1979), and a precise harmonic generator for testing THD measurements.

## Decision

- **The API.**
  - Python: `chebyshev_shaper(samples, weights)` in `dsp`.
  - C#: `Dsp.ChebyshevShaper(ReadOnlySpan<double> samples, ReadOnlySpan<double> weights)`.
  - Real output, one per sample.
- **The value.**
  - `y = Σ_{k=0}^{K} w_k·T_k(x)`, with `K + 1` the number of weights.
  - It is evaluated by Clenshaw's recurrence, which is stable on `[−1, 1]`. With
    `b_{K+1} = b_{K+2} = 0`, `b_k = w_k + (2·x·b_{k+1} − b_{k+2})` for `k = K … 1`, computed in
    that order. Then `y = w_0 + (x·b_1 − b_2)`.
  - With one weight, `y = w_0`.
  - For an input `cos θ`, harmonic `k` comes out at amplitude `w_k`, with `w_0` as a DC offset.
- **The rules.**
  - `samples` real, one-dimensional, non-empty, finite and within `[−1, 1]`. Outside it the
    polynomials grow as `|x|^K` and the harmonic property no longer holds.
  - `weights` real, one-dimensional, non-empty and finite.

## Consequences

- **Vectors.**
  - Expected values come from the three-term recurrence `T_0 = 1`, `T_1 = x`,
    `T_{k+1} = 2·x·T_k − T_{k−1}`, summed in exact rationals and rounded once. That is the
    definition, not Clenshaw's order.
  - Clenshaw's rounding error on `[−1, 1]` grows about as `K²` roundings, so with up to ten
    weights the tolerance is `abs 1e-12, rel 1e-12`.
  - The Python tests check the harmonic property on a sampled cosine.
