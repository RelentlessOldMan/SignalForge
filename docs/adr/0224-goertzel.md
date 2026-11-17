# ADR 0224: Goertzel

Status: accepted, 2026-11-17.

## Context

Tone detection (DTMF, pilot tones, a test signal's fundamental) needs the spectrum at a few
frequencies, not at all of them. An FFT works out every bin, and its bins fall only at multiples
of `fs/N`. The Goertzel recursion gives the DTFT at any frequency in `O(N)` per frequency, with
one real multiply per sample.

## Decision

- **The API.**
  - Python: `goertzel(samples, sample_rate, frequencies)` in `spectral`.
  - C#: `Spectral.Goertzel`, for real or complex samples.
  - Both return one complex value per frequency.
- **The value.**
  - It is the unscaled DTFT `X(f) = Σ_{n=0}^{N−1} x[n] e^(−2πi f n/fs)`.
  - It has the same sign and origin as `fft`, so at `f = k·fs/N` it equals FFT bin `k`.
  - Frequencies need not be bins. Negative frequencies and frequencies past `fs/2` are allowed,
    and they alias as the DTFT does.
- **The algorithm.** Let `ω = 2πf/fs`.
  - The recursion is `s[n] = x[n] + 2cos ω·s[n−1] − s[n−2]`, with `s[−1] = s[−2] = 0`.
  - Then `X = e^(−iω(N−1))·(s[N−1] − e^(−iω)·s[N−2])`.
  - The final phase factor makes the result the DTFT with origin at `n = 0`, rather than the
    value at the last sample.
  - The recursion is linear, so complex samples run it with complex states.
- **The rules.**
  - The samples must be finite and non-empty.
  - `sample_rate` must be positive and finite.
  - The frequencies must be finite and non-empty.

## Consequences

- **Precision.** The recursion's round-off grows with `N` for `ω` near 0 or `π`. The vectors use
  short inputs, and long inputs at extreme frequencies should use `fft` or a windowed method.
- **Vectors.**
  - The expected values are direct DTFT sums in the generator, without the recursion.
  - They are cross-checked against closed forms:
    - all ones gives the geometric series `(1 − e^(−iωN))/(1 − e^(−iω))`;
    - an impulse at `n_0` gives `e^(−iωn_0)`;
    - a cosine on bin `k` gives `N/2`.
