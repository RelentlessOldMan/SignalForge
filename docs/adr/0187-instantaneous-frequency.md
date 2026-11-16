# ADR 0187: Instantaneous frequency

Status: accepted, 2026-11-16. It builds on the analytic signal of ADR 0185.

## Context

The instantaneous frequency of a real signal is the rate of change of its analytic signal's
phase. It is the basis for chirp, FM and frequency-drift measurements. Implementations differ
in three ways:

- some unwrap the phase and difference it, others take the angle of `z[n+1]·conj z[n]`;
- some return `N − 1` values, others pad to `N`;
- they report in Hz or in radians per sample.

## Decision

- **The API.** In `spectral`:
  - Python: `instantaneous_frequency(samples, sample_rate)`.
  - C#: `Spectral.InstantaneousFrequency(samples, sampleRate)`.
- **The definition.** `f[n] = fs/(2π)·atan2(Im w, Re w)`, where `w = z[n+1]·conj z[n]` for
  `n = 0 … N−2` and `z` is the `analytic_signal` of ADR 0185.
  - The result is `N − 1` values in Hz, in `(−fs/2, fs/2]`.
  - No unwrapping is needed: each step is measured on its own.
  - The value can be negative, which happens where a weak tone beats against a strong one.
  - A step where `z` is zero gives `atan2(0, 0) = 0`. Rounding usually leaves a tiny product
    there instead, so the value at such a step is not defined.
- **The rules.**
  - The input follows the analytic-signal rules, with at least two samples.
  - `sample_rate` is finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors.**
  - Cosines and sines at bin `k`, for odd and even `N`, give the constant `k·fs/N`.
  - A DC offset plus a bin tone, and two bin tones, have closed-form analytic signals
    (`c + e^{jθ}`, `e^{jθ₁} + a·e^{jθ₂}`); the expected values are the angles of their steps.
  - Every step angle is kept away from ±π, where the sign of a rounded zero would decide.
