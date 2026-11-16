# ADR 0129: Spectral flux

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

Spectral flux measures how much a PSD changed from one frame to the next. It is the standard
onset feature of audio analysis, and it detects a burst or a hop in RF. The definitions vary in
three ways:

- The difference can be used as it is, or only its rises (rectified).
- The frames can be normalized first, or not.
- The norm can be L1 or L2.

Libraries also sum over bins. That ignores bin widths and band edges that cut bins.

## Decision

- **The API.**
  - Python: `spectral_flux(frequencies, previous, current, *, band=None, span=None,
    normalize=True, rectify=True)`, returning a float.
  - C#: `Spectral.SpectralFlux(frequencies, previous, current, band, span, normalize, rectify)`.
- **The model.** Both frames are validated as PSDs on the same `frequencies`, with the channel
  power rule's bins and the same `span`. Each one is a step density on the pieces `[a_k, b_k]` of
  the spectral moments.
- **Normalizing.** With `normalize`, each frame's densities are divided by that frame's own power
  over the band, so the flux ignores a change in overall level.
- **The difference.** `Δ_k = current_k − previous_k`. With `rectify`, it becomes `max(Δ_k, 0)`,
  so only rises count.
- **The result.** `flux = sqrt(Σ Δ_k² (b_k − a_k))`, which is `sqrt(∫ Δ² df)`, the L2 norm of
  the step function.
- **The rules.**
  - Both frames must be valid PSDs of the same length as `frequencies`.
  - The band rules are those of spectral flatness.
  - With `normalize`, each frame needs positive power over the band.
  - Anything else is `invalid_argument`.

## Consequences

- **Units.** The flux is in PSD·√Hz, or 1/√Hz when normalized. It is a distance between
  densities, so it is comparable between frames of one analysis, not across bin widths.
- **Defaults.** Normalizing and rectifying is the common onset form, so both are on by default.
- **Only L2.** Only the L2 norm is given. An L1 form would be a separate decision.
- **Vectors.** These are worked by hand with Fractions; the squared result is rational:
  - Identical frames give 0.
  - A frame against its own double gives 0 normalized.
  - One bin rising.
  - Rises and falls, rectified and not.
  - A cut band.
  - The span.
  - The errors.
- **Tests.**
  - Swapping the frames and not rectifying gives the same flux.
  - Rectified fluxes in the two directions add up, in squares, to the unrectified flux.
  - Scaling a frame changes nothing when normalized.
