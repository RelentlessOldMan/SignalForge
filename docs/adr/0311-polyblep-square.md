# ADR 0311: PolyBLEP square

Status: accepted, 2026-11-18.

## Context

The PolyBLEP sawtooth (ADR 0310) smooths its one jump with a two-sample polynomial residual.
A square with duty `d` has two jumps a cycle, a rise of `2A` at `u = 0` and a fall of `2A` at
`u = d`. The same residual applied at each edge, with the sign of that edge's jump, gives a
cheap near-alias-free square for any duty. The band-limited square (ADR 0309) is exact but
fixed at half duty and costs one sine per harmonic.

## Decision

- **The API.**
  - Python: `polyblep_square(sample_rate, num_samples, frequency, duty=0.5, amplitude=1,
    phase=0)` in `waveforms`.
  - C#: `Waveforms.PolyblepSquare`, same arguments.
  - Real output, `phase` in cycles.
- **The value.**
  - `u` is the oscillators' phase, and `dt = |f|/fs`. `r(·)` is the residual of ADR 0310.
  - `v = u − d`, plus 1 when `u < d`. The sign of a floating-point difference is exact, so
    `v < 0` exactly when `u < d`, and the naive square and the falling residual switch on
    the same samples.
  - `y = s + A·r(u) − A·r(v)`, with `s` the naive square (`A` for `u < d`, else `−A`).
  - With `d = 0` or `d = 1` the two residuals cancel, exactly for `d = 0` and to a rounding
    for `d = 1`, and the output is the naive constant.
  - The residuals depend only on `u`, so a negative frequency needs no change of sign.
- **The rules.**
  - As for the square: `sample_rate` positive and finite, `num_samples` an integer of at least
    0, `duty` in [0, 1], `amplitude` and `phase` finite.
  - As for the PolyBLEP sawtooth: `frequency` finite with `|f| ≤ fs/2`.
  - Near `d = 0` or `d = 1` the two edges' residual regions overlap. They add, as in the
    usual PolyBLEP square.

## Consequences

- **Vectors.**
  - Expected values come from the rule in exact rationals, rounded once.
  - At each edge the jump of the naive square cancels the jump of the residual, so the output
    is continuous in `u`. A rounding that moves a sample across an edge changes it by a
    rounding only.
  - The tolerance is `abs 1e-12, rel 1e-12`.
  - The Python tests check that the aliased energy is far below the naive square's.
- **Code.** The residual becomes a shared helper used by both PolyBLEP oscillators.
