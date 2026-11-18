# ADR 0290: Bass enhancer

Status: accepted, 2026-11-17.

## Context

Small speakers cannot reproduce low bass, but the ear hears a fundamental from its harmonics
(the missing fundamental). A bass enhancer adds harmonics of the low band so the bass is heard
on speakers that cannot play it. It is the exciter (ADR 0288) mirrored: distort the band below
the crossover instead of above it, then keep only what the distortion added above the
crossover, so the low band itself is not changed.

## Decision

- **The API.**
  - Python: `bass_enhancer(samples, order, cutoff, sample_rate, drive, mix)` in `dsp`.
  - C#: `Dsp.BassEnhancer(samples, order, cutoff, sampleRate, drive, mix)`.
  - Real samples only.
- **The value.**
  - `l = crossover_split(samples, order, cutoff, fs).low`.
  - `c = soft_clip(drive·l)/drive`.
  - `h = crossover_split(c, order, cutoff, fs).high`: the harmonics above the crossover.
  - `y = x + mix·h`.
  - The cubic clipper is odd, so it adds odd harmonics: the third first.
- **The rules.**
  - The splitter's rules for `samples`, `order`, `cutoff` and `fs`.
  - `drive` finite and positive.
  - `mix` in [0, 1].

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription. Both bands are the stdlib Butterworth
    sections of ADR 0285's generator in exact rationals, each rounded once; the clipper and the
    sum are stdlib floats.
  - The tolerance is `abs 1e-13, rel 1e-11`.
