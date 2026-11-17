# ADR 0238: Envelope follower

Status: accepted, 2026-11-17.

## Context

Level meters, compressors, gates and AGC loops follow a signal's magnitude with a peak detector.
It rises quickly (the attack) and falls slowly (the release). The analytic envelope from the
Hilbert transform is not causal and has no such asymmetry.

## Decision

- **The API.**
  - Python: `envelope_follower(samples, attack, release)` in `dsp`.
  - C#: `Dsp.EnvelopeFollower(samples, attack, release)`, for real or complex samples.
  - Both return real values.
- **The value.**
  - `r[n] = |x[n]|`, and `e[−1] = 0`.
  - `e[n] = r[n] + c·(e[n−1] − r[n])`, computed in that order. `c = attack` when
    `r[n] > e[n−1]`, and `c = release` otherwise.
  - `attack` and `release` are one-pole coefficients per sample, not times. 0 follows the input
    at once. For a time constant `τ` at rate `fs`, use `exp(−1/(τ·fs))`.
  - A constant input `r` from rest gives `e[n] = r·(1 − attack^(n+1))`.
  - A drop to 0 decays as `release^k`.
- **The rules.**
  - `attack` and `release` must be finite, in `[0, 1)`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The generator runs the definition in exact rational arithmetic. The coefficients are binary
    fractions, and the complex samples have exact magnitudes, such as `3 + 4i`.
  - It checks the closed forms above. The comparisons it makes are never ties.
