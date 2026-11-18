# ADR 0291: Octave-down effect

Status: accepted, 2026-11-17.

## Context

The analog octave-down pedal divides the frequency with a flip-flop: a sign that toggles once
per input cycle has half the input's frequency. Multiplying the rectified signal by that sign
gives, for a sine, a wave whose halves alternate in sign every input period. Its period is two
input periods, so its lowest component is an octave down. ADR 0289 is the octave up.

## Decision

- **The API.**
  - Python: `octave_down(samples, mix)` in `dsp`.
  - C#: `Dsp.OctaveDown(samples, mix)`.
  - Real samples only.
- **The value.**
  - A sign `s` starts at +1. Before sample `n ≥ 1` is used, `s` flips if `x[n−1] < 0 ≤ x[n]`,
    a rising zero crossing. The first sample never flips it.
  - `wet[n] = s·|x[n]|`.
  - `y = (1 − mix)·x + mix·wet`, the dry/wet blend of the other effects.
  - There is no hysteresis. Noise around zero toggles the sign, so callers low-pass a noisy
    input first, as the pedals do.
- **The rules.**
  - The samples must be real, finite and at least one.
  - `mix` in [0, 1].

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription of the rule. Each output is one product
    and one blend in floats.
  - The tolerance is `abs 1e-15, rel 1e-15`.
