# ADR 0143: Harmonic-to-noise ratio

Status: accepted, 2026-11-16. It builds on the band energy ratio (ADR 0134) and the harmonic
series (ADR 0139).

## Context

The harmonic-to-noise ratio compares the power at the harmonics of a fundamental with the power
everywhere else. Estimators work in the time domain (autocorrelation) or on a spectrum. The
spectral ones differ on four things:

- how wide a band around each harmonic counts as harmonic;
- whether a bin is split between the two parts;
- where DC and the bins below the fundamental go;
- whether the answer is a ratio or in dB.

## Decision

- **The API.**
  - Python: `harmonic_to_noise(frequencies, psd, fundamental, half_width)`, returning
    `HarmonicToNoise(harmonic, noise, ratio, ratio_db)`.
  - C#: `Spectral.HarmonicToNoise(frequencies, psd, fundamental, halfWidth)`, returning the
    record `HarmonicToNoise(Harmonic, Noise, Ratio, RatioDb)`.
  - `fundamental` would usually come from `harmonic_series`.
- **The bins.**
  - Bin `k` at frequency `f_k` carries the power `psd_k·Δ`, where `Δ` is the bin spacing, as in
    the band energy ratio.
  - A bin is harmonic when `m = ⌊f_k/f0 + 1/2⌋` is at least 1 and `|f_k − m·f0| ≤ half_width`.
  - Every other bin is noise. That includes DC and anything below `f0/2`.
  - Whole bins are sorted, and none is split. `half_width = 0` takes only bins that fall exactly
    on a harmonic.
- **The value.**
  - `harmonic` and `noise` are the sums of the two sets' bin powers.
  - `ratio = harmonic / noise` and `ratio_db = 10 log10(ratio)`.
  - Zero noise gives `+inf` for both. Zero harmonic power gives a ratio of 0 and `−inf` dB.
    Both zero is `invalid_argument`. This follows the band energy ratio.
- **The rules.**
  - The bins follow the band energy ratio's rules: 1-D, the same length, at least two,
    ascending and evenly spaced, and a finite, non-negative PSD.
  - `fundamental` is finite and positive.
  - `0 ≤ half_width < fundamental/2`, so the bands of neighbouring harmonics never meet.
  - Anything else is `invalid_argument`.

## Consequences

- **Choosing the width.** Sorting whole bins keeps the result exact and simple. The price is that
  the result jumps as `half_width` crosses a bin. Choose `half_width` to cover the window's main
  lobe, for example two bins for a Hann window.
- **Harmonics are not capped.** Every harmonic up to the top bin counts. To cap them, pass a
  shorter PSD.
- **Vectors.** These are worked by hand in Fractions:
  - exact harmonics with zero width.
  - a width that takes neighbouring bins.
  - a fundamental between bins.
  - no noise.
  - no harmonic power.
  - the errors.
- **Tests.**
  - Scaling the PSD leaves the ratio unchanged.
  - A sine in white noise gives about the expected ratio, as a statistic.
