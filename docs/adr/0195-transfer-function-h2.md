# ADR 0195: Transfer-function estimate (H2)

Status: accepted, 2026-11-16. It goes with H1 (ADR 0193).

## Context

H1 (`Pxy/Pxx`) is biased low when the measured input carries noise. H2 (`Pyy/Pyx`) is unbiased
in that case and biased high for output noise. Comparing the two is a standard check, because
`H1/H2` is the coherence.

## Decision

- **The API.** In `spectral`, for real input:
  - Python: `transfer_function_h2(x, y, sample_rate, *, nperseg=None, noverlap=None,
    window="hann", beta=None, detrend="none", nfft=None)`.
  - C#: `Spectral.TransferFunctionH2`, with the same arguments.
  - Both return the `TransferFunction` result of ADR 0193.
- **The definition.** For each bin, `H2[k] = Σ_s |Y_s[k]|² / Σ_s conj Y_s[k]·X_s[k]`.
  - The segments are those of `transfer_function`.
  - The denominator is `conj Sxy`, with `Sxy` as in H1.
  - `H2` is NaN in both parts where that sum is exactly 0.
  - Then `H1/H2 = |Sxy|²/(Sxx·Syy)`, which is the coherence, a real number.
- **The rules.** They are those of `transfer_function`.

## Consequences

- **Noise-free vectors.** They give `H2 = H1`: an impulse through an FIR, a scaled copy, and a
  zero-power input bin.
- **Inconsistent segments.** One vector has segments that disagree: H1 there is `1/3`, H2 is `3`
  and the coherence is `1/9`. Where `Sxy = 0`, H1 is 0 and H2 is NaN.
