# ADR 0120: Spectral flatness

Status: accepted, 2026-11-16. It extends the spectral measurements (conventions: Spectra).

## Context

How noise-like a spectrum is gets summed up by its spectral flatness (Wiener entropy). This is
the geometric mean of the PSD over its arithmetic mean. It is 1 for a flat (white) spectrum, and
it falls towards 0 as the power gathers into a few bins. It is used to tell tones from noise, to
judge how white a whitening filter's output is, and as an audio feature. SignalForge measures band
powers (channel power, ACPR, NPR) but nothing measures this shape.

## Decision

- Python `spectral_flatness(frequencies, psd, *, band=None, span=None)` and C#
  `Spectral.SpectralFlatness(frequencies, psd, band, span)`.
- **The bins and the weights.**
  - The bins are those of the channel power rule (same validation, same `span`).
  - Bin `k` has edges `[left_k, right_k]` and density `d_k = P_k / (right_k − left_k)`, where
    `P_k` is its power. This is the PSD value, except in a span-clipped edge bin, which keeps its
    whole power as it does for channel power.
  - Bin `k`'s weight `w_k` is the width of its overlap with `band = (low, high)`. With no band,
    the band is the whole spectrum, `[left_0, right_last]`.
- **The result.** Let `W = Σ w_k`, `G = exp(Σ w_k·ln d_k / W)` and `A = Σ w_k·d_k / W`. The
  result is `SpectralFlatness(geometric_mean=G, arithmetic_mean=A, flatness=G/A,
  flatness_db=10·log10(G/A))`.
  - A bin with `w_k > 0` and `d_k = 0` makes `G = 0`, so `flatness = 0` and `flatness_db = −∞`.
  - Bins with `w_k = 0` are left out.
- **The rules.**
  - The band's edges must be finite with `low < high`. The band must lie inside the spectrum
    within ACPR's slack.
  - `A > 0` is required.
  - Anything else is `invalid_argument`.

## Consequences

- **Weights.** Weighting by overlap width makes the result a mean over frequency, not over
  bins. A band edge that cuts a bin counts the cut fraction, as the channel power rule does, so a
  band of any width gives a defined answer.
- **The bound.** By the AM-GM inequality, `0 ≤ flatness ≤ 1`, with 1 only for a constant density.
- **Vectors.** These are short PSDs worked by hand: flat, two-level and three-level spectra with
  whole and cut bins, a zero bin, a clipped span, and the errors. The closed forms are powers of
  2, for example `G = 4^{3/4}`.
- **Tests.**
  - A PSD at level `x` on a fraction `a` of the band and `y` on the rest has the closed form
    `x^a·y^(1−a) / (a·x + (1−a)·y)`.
  - A periodogram of a pure tone is close to 0.
  - Scaling the PSD by a constant does not change the flatness.
  - A rectangular periodogram of white noise has exponential bins, so its flatness is close to
    `exp(−γ) ≈ 0.561`, where γ is Euler's constant.
