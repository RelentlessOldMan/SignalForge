# ADR 0130: Spectral decrease

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

Spectral decrease is an audio feature for how fast the spectrum falls away from its first bin.
The library form is `Σ_{k≥1} (P_k − P_0)/k / Σ_{k≥1} P_k` over the bins' powers. It counts
bins, so a band edge that cuts a bin has no meaning in that form. A truly continuous version,
`∫ (d(f) − d(low)) / (f − low) df`, gives logs, so its vectors could not be exact.

## Decision

- **The API.**
  - Python: `spectral_decrease(frequencies, psd, *, band=None, span=None)`, returning a float.
  - C#: `Spectral.SpectralDecrease(frequencies, psd, band, span)`.
- **The pieces.** The PSD is a step density on the pieces `[a_k, b_k]` of the spectral moments,
  with density `d_k`, width `w_k = b_k − a_k` and midpoint `m_k`. Piece 0 is the first piece
  in the band.
- **The value.** `decrease = Σ_{k≥1} (d_k − d_0) w_k · δ/(m_k − m_0) / Σ_{k≥1} d_k w_k`,
  where `δ` is the bin spacing. It is dimensionless.
- **Uncut bins.** When no bin is cut, `w_k = δ` and `m_k − m_0 = kδ`, so this is exactly the
  library form on bin powers.
- **The rules.**
  - The band rules are those of spectral flatness.
  - The band needs at least two pieces, and positive power after the first.
  - Anything else is `invalid_argument`.

## Consequences

- **What it means.** A flat PSD gives 0, a falling one gives a negative value, and a rising one a
  positive value. It depends on where the first bin falls, as the library form does.
- **Vectors.** These are worked by hand with Fractions:
  - flat gives 0.
  - The ramp `[4, 3, 2, 1]` gives −1/2.
  - The ramp `[1, 2, 3, 4]` gives (1 + 1 + 1)/9, which is 1/3.
  - A cut band and the span.
  - The errors.
- **Tests.**
  - Scaling the PSD changes nothing.
  - Stretching the axis changes nothing.
  - Uncut bins match the library form computed directly.
