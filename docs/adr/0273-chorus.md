# ADR 0273: Chorus

Status: accepted, 2026-11-17.

## Context

A chorus makes one voice sound like several by adding copies of it, each through its own slowly
swinging delay. The vibrato (ADR 0271) is one such copy. Spreading the copies' oscillator
phases evenly around the circle keeps their delays apart, so they do not sweep together the way
a flanger does. The delays are usually longer than a flanger's, about 10 to 30 ms, and the result
is a thickening, not a moving comb.

## Decision

- **The API.**
  - Python: `chorus(samples, delay, depth, rate, sample_rate, voices, mix)` in `dsp`.
  - C#: `Dsp.Chorus(samples, delay, depth, rate, sampleRate, voices, mix)`.
  - Real and complex; the output is the same kind.
- **The value.**
  - Voice `k` in `[0, V)` is the vibrato with delay
    `delay + depth·cos((2π·rate)·(n/fs) + φₖ)`, where `φₖ = (2π·k)/V`.
  - The wet signal is `w = (v₀ + v₁ + … + v_{V−1})/V`, summed in voice order.
  - `y = x·(1 − mix) + w·mix`, evaluated in that order.
  - With `V = 1` it is the flanger (ADR 0272).
  - A complex sample is handled part by part.
- **The rules.**
  - The vibrato's rules apply.
  - `voices` must be an integer `≥ 1`.
  - `mix` must be finite and in `[0, 1]`.
- **The vibrato** gains no public phase argument; the voices share a private reader that takes
  the oscillator phase.

## Consequences

- **Vectors.**
  - The cases with `depth = 0` are exact.
  - Modulated cases reuse the vibrato's stdlib transcription with the phase added.
  - The tolerance is `abs 1e-14, rel 1e-14`.
