# ADR 0288: Harmonic exciter

Status: accepted, 2026-11-17.

## Context

An exciter brightens a signal by adding harmonics of its upper band. Unlike a treble boost it
adds content that was not there, so it can brighten a dull recording. The common form splits off
the high band, distorts it gently and mixes the result back with the full signal. ADR 0285 gives
the split and ADR 0250 the soft clipper.

## Decision

- **The API.**
  - Python: `exciter(samples, order, cutoff, sample_rate, drive, mix)` in `dsp`.
  - C#: `Dsp.Exciter(samples, order, cutoff, sampleRate, drive, mix)`.
  - Real samples only.
- **The value.**
  - `h = crossover_split(samples, order, cutoff, fs).high`.
  - `y = x + mix·soft_clip(drive·h)/drive`, element by element.
  - The input passes unchanged, so this is not a dry/wet blend: `mix` is the amount added.
  - Dividing by `drive` keeps the added band's small-signal gain at 1, so `drive` sets only
    how much it distorts.
- **The rules.**
  - The splitter's rules for `samples`, `order`, `cutoff` and `fs`.
  - `drive` finite and positive.
  - `mix` in [0, 1].

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription. The high band is the stdlib Butterworth
    sections of ADR 0285's generator in exact rationals; the clipper and the sum are stdlib
    floats.
  - The tolerance is `abs 1e-13, rel 1e-11`.
