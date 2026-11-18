# ADR 0310: PolyBLEP sawtooth

Status: accepted, 2026-11-17.

## Context

The band-limited sawtooth (ADR 0307) is exact but costs one sine per harmonic per sample. The
PolyBLEP method (Välimäki and others, 2007) gets most of the way for a fixed small cost: it
subtracts from the naive sawtooth a two-sample polynomial that smooths the jump, a cheap
stand-in for the band-limited step. Aliasing drops by more than an order of magnitude at
ordinary pitches, which is why it is the usual choice in software synthesizers.

## Decision

- **The API.**
  - Python: `polyblep_sawtooth(sample_rate, num_samples, frequency, amplitude=1, phase=0)` in
    `waveforms`.
  - C#: `Waveforms.PolyblepSawtooth`, same arguments.
  - Real output, `phase` in cycles.
- **The value.**
  - `u` is the oscillators' phase, and `dt = |f|/fs`.
  - The residual: for `u < dt`, `t = u/dt` and `r = t + t − t·t − 1`; otherwise for
    `u > 1 − dt`, `t = (u − 1)/dt` and `r = t·t + t + t + 1`; otherwise `r = 0`. The tests are
    made in that order.
  - `y = A·((2·u − 1) − r)`.
  - The residual depends only on `u`, as the band-limited sawtooth does, so a negative
    frequency needs no change of sign. At `f = 0` the residual is 0 and the output is the
    naive shape.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `frequency` finite with `|f| ≤ fs/2`, so the two residual regions do not overlap.
  - `amplitude` and `phase` finite.

## Consequences

- **Vectors.**
  - Expected values come from the rule in exact rationals, rounded once. The residual is 0 at
    both edges of its regions, so a rounding that moves a sample across an edge changes it by
    a rounding only.
  - The tolerance is `abs 1e-12, rel 1e-12`.
  - The Python tests check that the aliased energy is far below the naive sawtooth's.
