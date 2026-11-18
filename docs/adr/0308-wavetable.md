# ADR 0308: Wavetable oscillator

Status: accepted, 2026-11-17.

## Context

A wavetable oscillator stores one cycle of any shape and plays it at any pitch by reading the
table at a moving phase. It is how sampled and drawn waveforms are played, and it is cheap: one
interpolated read per sample. Read with linear interpolation, it plays back exactly what is
between the table's points; the table's own harmonics above the Nyquist frequency of the
playback alias, which is the caller's to avoid by drawing the table smooth enough.

## Decision

- **The API.**
  - Python: `wavetable(table, sample_rate, num_samples, frequency, phase=0)` in `waveforms`.
  - C#: `Waveforms.Wavetable(table, sampleRate, numSamples, frequency, phase = 0)`.
  - `table` holds one cycle of `L` real samples. The output is real, with `phase` in cycles as
    for the oscillators.
- **The value.**
  - `u` is the oscillators' phase: `t = f·(n/fs) + phase`, `u = t − floor(t)`.
  - `p = u·L`, `i = floor(p)`, `r = p − i`. If `i` reaches `L`, which rounding can make happen
    just below the end of a cycle, it is taken as `i − L`.
  - `y = T[i]·(1 − r) + T[(i + 1) mod L]·r`. The read wraps from the last entry back to the
    first, so the cycle joins up.
  - A one-entry table gives a constant.
- **The rules.**
  - The table must be real, finite and at least one entry.
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `frequency` and `phase` finite.

## Consequences

- **Vectors.**
  - Expected values come from the read in exact rationals, rounded once.
  - The tolerance is `abs 1e-12, rel 1e-12`.
