# ADR 0272: Flanger

Status: accepted, 2026-11-17.

## Context

A flanger adds a signal to a copy of itself delayed by a few milliseconds that sweep. The sum is
a comb filter whose notches move with the delay. The wet path is the vibrato (ADR 0271). The
flanger fixes the mix as a crossfade between dry and wet, so the gain never exceeds 1 for a
constant signal. At `mix = 1/2` the notches go to zero.

## Decision

- **The API.**
  - Python: `flanger(samples, delay, depth, rate, sample_rate, mix)` in `dsp`.
  - C#: `Dsp.Flanger(samples, delay, depth, rate, sampleRate, mix)`.
  - Real and complex; the output is the same kind.
- **The value.**
  - `v = vibrato(samples, delay, depth, rate, sample_rate)`.
  - `y = x·(1 − mix) + v·mix`, evaluated in that order.
  - A complex sample is weighted part by part.
- **The rules.**
  - The vibrato's rules apply.
  - `mix` must be finite and in `[0, 1]`.

## Consequences

- **Vectors.**
  - Constant-delay cases are exact.
  - Modulated cases reuse the vibrato's stdlib transcription.
  - The tolerance is `abs 1e-14, rel 1e-14`.
- **No feedback.** A feedback flanger feeds the wet path back into the delay line. It would need
  its own slice.
