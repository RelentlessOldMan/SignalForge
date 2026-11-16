# ADR 0125: Spectral crest factor

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

The spectral crest factor is the PSD's peak divided by its mean across a band. It is the audio
feature that goes with the flatness ([ADR 0120](0120-spectral-flatness.md)):

- A tone gives a high crest.
- Noise gives a low one.
- A flat band gives exactly 1.

It is not the time-domain crest factor (PAPR), which the power statistics already give.

## Decision

- Python `spectral_crest(frequencies, psd, *, band=None, span=None) -> SpectralCrest(peak,
  mean, crest, crest_db)` and C# `Spectral.SpectralCrest(frequencies, psd, band, span)`, with the
  record `SpectralCrest(Peak, Mean, Crest, CrestDb)`.
- **The bins.** These are the flatness's bins: the channel power rule's bins, with the same
  `span`. Bin `k` has density `d_k = P_k / (right_k − left_k)` and weight `w_k`, the width of its
  overlap with `band` (by default, the whole spectrum).
- **The result.**
  - `mean = Σ w_k d_k / Σ w_k`, the flatness's arithmetic mean.
  - `peak = max d_k` over the bins with `w_k > 0`, however small the overlap.
  - `crest = peak / mean`.
  - `crest_db = 10·log10(peak) − 10·log10(mean)`, because both are power densities.
- **The rules.**
  - The band rules are those of spectral flatness.
  - `mean > 0` is required.
  - Anything else is `invalid_argument`.

## Consequences

- **Range.** `crest ≥ 1` always holds, and it equals 1 only when every weighted bin is the same.
- **Partial overlap.** A bin that only touches the band still counts at its full density for
  the peak, as it does in the flatness. The answer then does not jump when a band edge crosses
  a bin's middle. The mean weights it by its overlap.
- **dB.** The dB is the difference of two logs, as for the flatness. It is not the log of the
  rounded ratio.
- **Vectors.** These are worked by hand:
  - A flat PSD gives 1 (0 dB).
  - A single bin in `N` gives `N`.
  - Uneven PSDs.
  - A band that cuts bins.
  - The span.
  - The errors.
- **Tests.**
  - Scaling the PSD changes nothing.
  - A tone in white noise has a crest near its height over the noise floor.
  - The crest is never below 1.
