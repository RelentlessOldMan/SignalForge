# ADR 0128: Spectral entropy

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

Spectral entropy measures how evenly a band's power spreads: a tone gives a low value, and white
noise the highest. The common form is the bin-count entropy `−Σ q_k ln q_k / ln N`, where `q_k`
is each bin's share of the power. It needs equal, whole bins. Once a band edge cuts a bin, `N`
is no longer well defined.

The step density of the spectral moments ([ADR 0121](0121-spectral-moments.md)) has an exact
differential entropy. That entropy depends on the axis units, but its exponential is a width in
Hz, the entropy bandwidth, which does not.

## Decision

- Python `spectral_entropy(frequencies, psd, *, band=None, span=None) ->
  SpectralEntropy(entropy, entropy_bandwidth, normalized)` and C# `Spectral.SpectralEntropy(
  frequencies, psd, band, span)`, with the record `SpectralEntropy(Entropy, EntropyBandwidth,
  Normalized)`.
- **The model.** This is the step density and pieces `[a_k, b_k]` of the spectral moments, with
  the band's `power`. The normalized density is `p_k = d_k / power` per Hz, and its share is
  `q_k = p_k (b_k − a_k)`.
- **The result.**
  - `entropy = −Σ q_k ln p_k` in nats, over the pieces with `d_k > 0`. This is `−∫ p ln p df`,
    with `0 ln 0 = 0`.
  - `entropy_bandwidth = exp(entropy)` in Hz.
  - `normalized = entropy_bandwidth / (high − low)`, which is in `(0, 1]`.
- **The rules.**
  - The band rules are those of spectral flatness.
  - `power > 0` is required.
  - Anything else is `invalid_argument`.

## Consequences

- **Reading the result.**
  - A flat band gives `entropy = ln W`, the bandwidth `W`, and `normalized` 1.
  - Power in a width `δ`, flat there, gives bandwidth `δ`.
  - The entropy is negative when the bandwidth is below 1 Hz. That is correct, which is why the
    normalized form uses the bandwidth and not `entropy / ln W`.
- **The bin-count form.** For `N` equal whole bins of width `δ`, the bin-count form is
  `(entropy − ln δ) / ln N`. It is not given separately.
- **Vectors.** These are worked by hand:
  - A flat PSD.
  - A single bin.
  - Two equal bins, with bandwidth 2.
  - Uneven shares.
  - A cut band.
  - The span.
  - The errors.
  The generator computes them as `ln power − Σ q_k ln d_k`, a different algebra from the
  libraries'.
- **Tests.**
  - Scaling the PSD changes nothing.
  - Stretching the axis by `s` multiplies the bandwidth by `s` and leaves `normalized` as it is.
  - A tone over a low floor gives a small `normalized`.
  - White noise gives `normalized` near `exp(γ − 1)`, about 0.655. Its bins are exponential with
    mean 1, and `E[X ln X] = ψ(2) = 1 − γ`, so `entropy → ln N − (1 − γ)` for `N` unit bins.
