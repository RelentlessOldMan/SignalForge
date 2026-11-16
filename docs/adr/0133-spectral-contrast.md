# ADR 0133: Spectral contrast

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

Spectral contrast is the dB gap between the loudest and quietest parts of a band. Audio
libraries take the mean of the top and bottom fraction α of a sub-band's bins after sorting.
That count of bins is rounded, and it ignores bin widths.

## Decision

- **The API.**
  - Python: `spectral_contrast(frequencies, psd, *, band=None, span=None, fraction=0.2)`,
    returning `SpectralContrast(peak, valley, contrast_db)`.
  - C#: `Spectral.SpectralContrast(frequencies, psd, band, span, fraction)`, returning the
    record `SpectralContrast(Peak, Valley, ContrastDb)`.
- **The pieces.** The PSD is a step density on the pieces of the spectral moments, with density
  `d_k` and width `w_k`. The band's total width is `W = Σ w_k`.
- **The peak.** The pieces are sorted by density, highest first. `peak` is the mean density over
  the first `αW` of width. A piece that straddles the limit counts only for the width needed.
- **The valley.** `valley` is the same mean taken lowest first.
- **The contrast.** `contrast_db = 10 log10(peak / valley)`. It is +∞ when the valley is 0.
- **The rules.**
  - `fraction` must be finite, with `0 < fraction ≤ 1/2`, so that the top and bottom never
    overlap.
  - The band rules are those of spectral flatness.
  - The band needs positive power.
  - Anything else is `invalid_argument`.

## Consequences

- **Units.** `peak` and `valley` are in the PSD's units, and `contrast_db` is in dB. A flat PSD
  gives 0 dB.
- **The half split.** With `fraction = 1/2`, the top and bottom split the band, so
  `(peak + valley)/2` is the band's mean density.
- **Vectors.** The peak and valley are worked by hand with Fractions; only the dB is not
  rational:
  - flat.
  - a ramp at several fractions, including ones that split a piece.
  - a cut band.
  - the span.
  - the errors.
  - A zero valley is not a vector, since JSON has no ∞. It is in the tests.
- **Tests.**
  - Scaling the PSD scales the peak and the valley and leaves the dB unchanged.
  - The half split gives the band's mean.
  - A zero valley gives +∞.
  - A tone over a floor gives a large contrast.
