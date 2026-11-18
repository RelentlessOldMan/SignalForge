# ADR 0271: Vibrato

Status: accepted, 2026-11-17.

## Context

A vibrato reads the signal back through a delay whose length swings under a low-frequency
oscillator. The pitch then rises and falls by the Doppler effect. The delay is fractional, so
it needs interpolation. Linear interpolation is the usual choice for modulated delays: it is
cheap, has no state, and is continuous in the delay, so a delay that crosses a whole sample does
not jump. The oscillator is built the same way as the tremolo and ring modulator carrier
(ADR 0260). The flanger, the next slice, mixes this output with the dry signal.

## Decision

- **The API.**
  - Python: `vibrato(samples, delay, depth, rate, sample_rate)` in `dsp`.
  - C#: `Dsp.Vibrato(samples, delay, depth, rate, sampleRate)`.
  - Real and complex; the output is the same kind.
  - `delay` and `depth` are in samples, as in the fractional delay (ADR 0040).
- **The value.**
  - `d[n] = delay + depth·cos((2π·rate)·(n/fs))`.
  - `p = n − d[n]`, `i = ⌊p⌋`, `f = p − i`.
  - `y[n] = x[i]·(1 − f) + x[i+1]·f`, evaluated in that order.
  - `x[k] = 0` for `k < 0`, so the signal starts from rest.
  - Since `d ≥ 0`, `i + 1 ≤ n` whenever `f > 0`. When `f = 0`, the second term is 0.
  - A complex sample is weighted part by part.
- **The rules.**
  - `delay` must be finite and `≥ 0`.
  - `depth` must be finite and in `[0, delay]`.
  - `rate` must be finite.
  - `sample_rate` must be finite and `> 0`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - A constant delay gives exact values: whole delays shift, and half delays average.
  - Modulated cases use a stdlib transcription with `math.cos` and `math.floor`.
  - A one-ulp difference in `cos` that moves `⌊p⌋` changes `y` by at most an ulp, because the
    interpolation is continuous.
  - The tolerance is `abs 1e-14, rel 1e-14`.
