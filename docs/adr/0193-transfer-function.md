# ADR 0193: Transfer-function estimate (H1)

Status: accepted, 2026-11-16. It uses the Welch segments of `coherence` (ADR 0192).

## Context

Estimating the frequency response from a measured input `x` to an output `y` is the core of
system identification and loudspeaker or room measurement. The common estimators differ in which
signal is assumed noisy:

- `H1 = Sxy/Sxx` is unbiased for noise on the output.
- `H2 = Syy/Syx` is unbiased for noise on the input.
- `Hv` is a compromise between the two.

## Decision

- **The API.** In `spectral`, for real input only:
  - Python: `transfer_function(x, y, sample_rate, *, nperseg=None, noverlap=None,
    window="hann", beta=None, detrend="none", nfft=None)`, returning
    `TransferFunction(frequencies, response, num_segments)`.
  - C#: `Spectral.TransferFunction`, with the same arguments.
- **The segments.** They are exactly those of `coherence` (and so of `welch_psd`).
- **The estimator.** H1. For bins `k = 0 … ⌊M/2⌋` at `k·fs/M`:
  - `H[k] = Σ_s conj X_s[k]·Y_s[k] / Σ_s |X_s[k]|²`.
  - The scaling and the one-sided doubling cancel.
  - Where `Σ|X_s|² = 0`, `H` is NaN in both parts.
  - With a single rectangular segment and `y` the circular convolution of `x` with `h`, `H` is
    the DFT of `h` wherever `X ≠ 0`.
- **The output.** `response` is complex. The magnitude and phase are left to the caller (`abs`,
  `angle`), as everywhere else.
- **The rules.** They are those of `coherence`: real, one-dimensional, finite, the same length,
  and anything `welch_psd` rejects is `invalid_argument`.

## Consequences

- **Vectors.** They are hand DFTs of short segments:
  - an impulse through a two-tap FIR;
  - a scaled copy over two segments;
  - two segments whose cross terms cancel;
  - a zero-power bin.
- **Not covered.** H2 and Hv can be added later under their own names.
