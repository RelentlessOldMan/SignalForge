# ADR 0194: Cross-spectral density

Status: accepted, 2026-11-16. It uses the segments of `coherence` (ADR 0192) and
`transfer_function` (ADR 0193).

## Context

The cross-spectral density `Pxy` is the building block of:

- coherence;
- transfer functions;
- noise-cancellation and array processing.

Callers need it scaled. Conventions differ on two points:

- the conjugate order, which flips the sign of the phase;
- the one-sided doubling.

## Decision

- **The API.** In `spectral`, for real input:
  - Python: `cross_spectral_density(x, y, sample_rate, *, nperseg=None, noverlap=None,
    window="hann", beta=None, detrend="none", nfft=None)`, returning
    `CrossSpectralDensity(frequencies, csd, num_segments)`.
  - C#: `Spectral.CrossSpectralDensity`, with the same arguments.
- **The definition.** For one-sided bins `k = 0 … ⌊M/2⌋` at `k·fs/M`:
  - `Pxy[k] = d_k·Σ_s conj X_s[k]·Y_s[k] / (K·fs·Σw²)`.
  - The segments are those of `coherence`, and `K` is their number.
  - `d_k = 2` except at DC and, for even `M`, Nyquist, where it is 1. This is the `welch_psd`
    doubling.
  - The conjugate order is that of `transfer_function`, so `H1 = Pxy/Pxx` and a `y` that lags
    `x` has a negative phase.
  - For `y = x`, `Pxy` is `welch_psd(x)` with a zero imaginary part.
- **Complex input.** It is not accepted. A two-sided form is left to a later ADR.
- **The rules.** They are those of `coherence`.

## Consequences

- **Vectors.** They are hand DFTs of short rectangular segments:
  - an impulse through a two-tap FIR, which exercises the doubling;
  - `y = x`, which equals the hand PSD;
  - two segments whose cross terms cancel.
