# ADR 0127: Spectral slope

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

The spectral slope, or tilt, says how fast a band's power falls with frequency. It is an audio
feature, and in RF it is the gain slope across a channel. It is a least-squares line through the
PSD, but two things vary between libraries:

- The fit can be in linear PSD or in dB.
- The bins can be points or widths.

## Decision

- **The API.**
  - Python: `spectral_slope(frequencies, psd, *, band=None, span=None, db=False) ->
    SpectralSlope(center, level, slope)`.
  - C#: `Spectral.SpectralSlope(frequencies, psd, band, span, db)`, with the record
    `SpectralSlope(Center, Level, Slope)`.
- **The fitted function.** `y` is the step density of the spectral moments, `d_k` on each piece
  `[a_k, b_k]`. With `db`, it is `10·log10(d_k)` instead.
- **The fit.** This is the continuous least-squares line through that step function over the
  band, `min ∫ (y(f) − level − slope·(f − center))² df`, with `center = (low + high)/2`. The
  pieces tile the band, so `∫ (f − center) df = 0`, and with `W = high − low`:
  - `level = Σ y_k (b_k − a_k) / W`, the band's mean of `y`.
  - `slope = Σ y_k ((b_k − center)² − (a_k − center)²)/2 / (W³/12)`.
- **Units.** The slope is in the PSD's units per Hz, or in dB per Hz with `db`.
- **The rules.**
  - The band rules are those of spectral flatness.
  - Linear: the band's power must be positive.
  - With `db`: every bin that overlaps the band must have a positive PSD.
  - Anything else is `invalid_argument`.

## Consequences

- **The staircase effect.** Bins are widths, so a PSD sampled from a line `β f` over `M` equal
  bins gives `β (1 − 1/M²)`, not `β`. The staircase flattens the line slightly. Fitting points
  would give `β`, but a band edge that cuts a bin would then move the answer unevenly.
- **The band's centre.** The level is given at the band's centre, so the fit does not depend on
  where zero is on the axis.
- **dB and zero bins.** A zero bin has no dB value. Clipping it to a floor would make the slope
  depend on that floor, so it is an error.
- **Vectors.** These are worked with Fractions through the uncentered 2×2 normal equations, a
  different route:
  - A flat PSD gives slope 0.
  - A sampled line gives `β (1 − 1/M²)`.
  - Uneven PSDs.
  - dB on powers of ten.
  - A cut band.
  - The span.
  - The errors.
- **Tests.**
  - A sampled line, for several `M`.
  - The level times `W` equals the band's power.
  - Mirroring the PSD negates the slope.
  - Shifting the axis changes only the center.
  - dB of a PSD that is exponential in frequency.
