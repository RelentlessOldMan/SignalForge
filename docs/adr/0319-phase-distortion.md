# ADR 0319: Phase-distortion oscillator

Status: accepted, 2026-11-18.

## Context

Phase distortion reads a cosine through a bent phase. The phase runs fast through the first
half of the cosine and slowly through the second, so the wave keeps the cosine's smooth peaks
but gains a steep edge. Moving the bend from the middle towards the start sweeps the sound from
a pure tone to a bright, sawtooth-like one, much as a lowpass filter opening would. It gives a
filter-like brightness control with a single table read and no filter.

## Decision

- **The API.**
  - Python: `phase_distortion(sample_rate, num_samples, frequency, knee, amplitude=1,
    phase=0)` in `waveforms`.
  - C#: `Waveforms.PhaseDistortion`, same arguments.
  - Real output, `phase` in cycles.
- **The value.**
  - `u[n]` is the oscillators' phase. `k = knee`.
  - `w = u/(2·k)` for `u < k`, else `w = 1/2 + (u − k)/(2·(1 − k))`. That is the piecewise linear
    map through `(0, 0)`, `(k, 1/2)` and `(1, 1)`.
  - `y = −A·cos(2π·w)`. The minus sign starts the wave at its trough, so the steep edge with a
    small `k` is a rise, like the rising ramp of the sawtooth.
  - `k = 1/2` gives `−A·cos(2π·u)`, a pure tone.
  - `w` is continuous and `cos` is periodic, so the wave is continuous at the knee and across
    the wrap. Its slope jumps at both, so the harmonics fall as `1/m²`.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `frequency`, `amplitude` and `phase` finite.
  - `knee` finite with `0 < knee < 1`.

## Consequences

- **Vectors.**
  - `w` comes from the rule in exact rationals and is rounded once. The generator takes
    `math.cos(2π·w)` of it.
  - `w` is continuous in `u`, so a rounding of `u` moves a sample by at most a rounding times
    `π/min(k, 1 − k)`.
  - The tolerance is `abs 1e-12, rel 1e-12`.
