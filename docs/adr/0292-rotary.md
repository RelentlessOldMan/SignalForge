# ADR 0292: Rotary-speaker effect

Status: accepted, 2026-11-17.

## Context

A rotary speaker cabinet splits the signal with a crossover. A spinning horn plays the treble
and a spinning drum the bass. As each turns toward and away from the listener its sound gets
louder and softer, and the horn's moving mouth also shifts the pitch. The parts exist: the
splitter (ADR 0285), vibrato (ADR 0271) and tremolo (ADR 0261).

## Decision

- **The API.**
  - Python: `rotary(samples, order, cutoff, horn_rate, drum_rate, delay, depth, tremolo_depth,
    sample_rate)` in `dsp`.
  - C#: `Dsp.Rotary(...)` with the same arguments in PascalCase.
  - Real samples only.
- **The value.**
  - `b = crossover_split(samples, order, cutoff, fs)`.
  - `horn = tremolo(vibrato(b.high, delay, depth, horn_rate, fs), horn_rate, tremolo_depth, fs)`.
  - `drum = tremolo(b.low, drum_rate, tremolo_depth, fs)`.
  - `y = horn + drum`.
  - The horn's vibrato and tremolo share one rotation and start in phase, with the LFO at its
    peak at `n = 0`. A real cabinet's phase offsets and the Doppler of the drum are left out.
- **The rules.**
  - The splitter's rules for `samples`, `order`, `cutoff` and `fs`.
  - The vibrato's rules for `delay` and `depth`: `0 ≤ depth ≤ delay`.
  - The rates are finite.
  - `tremolo_depth` in [0, 1].

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription. The bands are the stdlib Butterworth
    sections of ADR 0285's generator in exact rationals, each rounded once. The vibrato read
    and the tremolo gains are transcribed from ADR 0271's and ADR 0261's generators in floats.
  - The tolerance is `abs 1e-13, rel 1e-11`.
