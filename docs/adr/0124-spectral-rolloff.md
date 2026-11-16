# ADR 0124: Spectral rolloff

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

The spectral rolloff is the frequency below which a given fraction of a band's power lies,
often 85 % or 95 %. It is an audio feature that goes with the centroid
([ADR 0121](0121-spectral-moments.md)) and the flatness ([ADR 0120](0120-spectral-flatness.md)).
Libraries often pick the first bin center where the running sum passes the fraction. That
answer can only be a bin center, and a band edge that cuts a bin moves it unevenly.

## Decision

- Python `spectral_rolloff(frequencies, psd, fraction, *, band=None, span=None)` and C#
  `Spectral.SpectralRolloff(frequencies, psd, fraction, band, span)` return a frequency in Hz.
- **The model.** The PSD is the step density of the spectral moments: `d_k = P_k / (right_k −
  left_k)` on each bin of the channel power rule, with the same `span`. Bin `k` overlaps `band`
  (by default, the whole spectrum) on `[a_k, b_k]`. The band's power is
  `power = Σ d_k (b_k − a_k)`.
- **The result.** The target is `fraction·power`. Walk the overlapping pieces upward and keep the
  running sum `S_k`, which includes piece `k`. Stop at the first piece where `S_k ≥ target`. The
  rolloff is `a_k + (target − S_{k−1}) / d_k`, limited to `[a_k, b_k]`.
- **The rules.**
  - `fraction` must be finite and in `(0, 1]`.
  - The band rules are those of spectral flatness.
  - `power > 0` is required.
  - Anything else is `invalid_argument`.

## Consequences

- **The stopping piece has power.** `S_{k−1} < target ≤ S_k` means piece `k` adds power, so
  `d_k > 0`. Empty bins that come before it are passed over, and the division is safe.
- **Ties.** If the target falls exactly at the end of a piece and the next bins are empty, the
  answer is that end. It is the lowest frequency where the fraction is reached.
- **Fraction 1.** This gives the top edge of the last bin with power, not the band's top edge.
- **Vectors.** These are worked by hand with Fractions, by the same walk:
  - A flat PSD gives `low + fraction·(high − low)`.
  - Uneven PSDs.
  - Empty bins before and after the answer.
  - A band that cuts bins.
  - The span.
  - The errors.
- **Tests.**
  - A flat PSD over a sweep of fractions.
  - Scaling the PSD changes nothing.
  - The rolloff only rises as the fraction grows.
  - At fraction 0.5, a symmetric PSD gives its centre.
