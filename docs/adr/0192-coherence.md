# ADR 0192: Magnitude-squared coherence

Status: accepted, 2026-11-16. It uses the Welch segmentation of ADR 0030 and ADR 0031.

## Context

The magnitude-squared coherence `|Pxy|²/(Pxx·Pyy)` measures, bin by bin, how much of `y` is a
linear function of `x`. It is used to check:

- transfer-function measurements;
- noise paths;
- which bands two sensors share.

It needs averaging over several segments: with one segment it is 1 wherever both spectra are
non-zero, whatever the signals. Implementations differ on several points:

- the segment arguments;
- the conjugate order;
- the scaling (which cancels);
- what happens where an auto-spectrum is zero.

## Decision

- **The API.** In `spectral`, for real input only:
  - Python: `coherence(x, y, sample_rate, *, nperseg=None, noverlap=None, window="hann",
    beta=None, detrend="none", nfft=None)`, returning `Coherence(frequencies, values,
    num_segments)`.
  - C#: `Spectral.Coherence`, with the same arguments.
- **The segments.** They are exactly those of `welch_psd`: the `nperseg`, `noverlap`, window,
  `beta`, detrending and zero-padding rules and defaults, applied to `x` and `y` alike.
- **The definition.** With `X_s` and `Y_s` the length-`M` transforms of windowed segment `s`,
  for bins `k = 0 … ⌊M/2⌋` at `k·fs/M`:
  - `Sxy = Σ_s X_s·conj Y_s`, `Sxx = Σ_s |X_s|²` and `Syy = Σ_s |Y_s|²`.
  - `C = min(1, |Sxy|²/(Sxx·Syy))`. The scale, the one-sided doubling and the conjugate order
    all cancel. The `min` only removes rounding above 1 (Cauchy–Schwarz).
  - `C` is NaN where `Sxx·Syy = 0`.
- **The rules.**
  - `x` and `y` are real, one-dimensional, finite and the same length.
  - Otherwise, and for anything `welch_psd` rejects, the error is `invalid_argument`.

## Consequences

- **Vectors.** They are worked by hand on short segments:
  - `y = c·x` gives 1 at every bin where `Sxx > 0`.
  - Segments whose bins agree in some places and cancel in others give values such as 0 and
    1/9.
  - A segment that detrends to zero gives NaN.
- **Unit tests.** Noise against filtered noise, and independent noise, are covered by
  statistics in unit tests.
