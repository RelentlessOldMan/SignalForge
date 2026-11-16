# ADR 0131: Spectral variation

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

Spectral variation measures how far the shape of the spectrum moved from one frame to the next.
It is one minus the normalized correlation of the two frames, which is the level-free companion
of the spectral flux (ADR 0129). Libraries sum over bins. That ignores bin widths and band edges
that cut bins.

## Decision

- **The API.**
  - Python: `spectral_variation(frequencies, previous, current, *, band=None, span=None)`,
    returning a float.
  - C#: `Spectral.SpectralVariation(frequencies, previous, current, band, span)`.
- **The model.** Both frames are step densities `d₀`, `d₁` on the pieces `[a_k, b_k]` of the
  spectral moments, with widths `w_k`. The pieces come from the same bins and the same `span`,
  as for the flux.
- **The value.** `variation = 1 − Σ d₀d₁w / sqrt(Σ d₀²w · Σ d₁²w)`, which is
  `1 − ∫ d₀d₁ df / (‖d₀‖ ‖d₁‖)`.
- **The rules.**
  - The band rules are those of spectral flatness.
  - Each frame needs positive power over the band.
  - Anything else is `invalid_argument`.

## Consequences

- **Range.** PSDs are non-negative, so the variation lies in [0, 1].
  - 0 means the same shape at any level.
  - 1 means the frames share no band.
- **Vectors.** These are worked by hand. The correlation squared is rational, and only its square
  root is in floating point:
  - identical frames.
  - a frame against its double.
  - disjoint frames.
  - `[1, 1, 0, 0]` against `[0, 1, 1, 0]`, which gives 1/2.
  - uneven frames.
  - a cut band.
  - the span.
  - the errors.
- **Tests.**
  - Swapping the frames gives the same value.
  - Scaling either frame changes nothing.
  - Random frames stay in [0, 1].
