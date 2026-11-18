# ADR 0314: PolyBLEP triangle

Status: accepted, 2026-11-18.

## Context

The naive triangle (ADR 0305) has no jumps, only two corners a cycle where the slope changes.
A corner aliases less than a jump, but still audibly at high pitches. The PolyBLEP
oscillators (ADRs 0310, 0311) smooth a jump with a two-sample residual. Integrating that
residual once gives the residual for a corner, often called PolyBLAMP. Its correction scales
with the change of slope a sample.

## Decision

- **The API.**
  - Python: `polyblep_triangle(sample_rate, num_samples, frequency, amplitude=1, phase=0)` in
    `waveforms`.
  - C#: `Waveforms.PolyblepTriangle`, same arguments.
  - Real output, `phase` in cycles.
- **The residual, derived here.**
  - Take the unit step and its two-sample PolyBLEP residual `e(x) = S(x) − H(x)`, where `x` is
    in samples from the edge. From ADR 0310 (jump `−2`, correction `−r`), `e = r/2`:
    `(1 + x)²/2` on `(−1, 0)` and `−(1 − x)²/2` on `[0, 1)`.
  - The ramp `max(x, 0)` is the integral of the step. Its residual is the integral of `e`
    from `−∞`, which is `E(x) = (1 − |x|)³/6` for `|x| < 1` and 0 elsewhere. `E` is
    continuous, and so is its slope.
- **The value.**
  - `u` is the oscillators' phase, and `dt = |f|/fs`.
  - The top corner is at `u = 0`, at distance `d₀ = min(u, 1 − u)` in cycles. The bottom
    corner is at `u = 1/2`, at distance `d₁ = |u − 1/2|`.
  - At the top the slope a sample changes by `−8·A·dt`, and at the bottom by `+8·A·dt`, for
    either sign of `f`. `E` is even, so the direction of travel does not matter.
  - `c = −E(d₀/dt) + E(d₁/dt)`, each term only when its distance is below `dt`, in that order.
  - `y = A·((4·|u − 1/2| − 1) + 8·dt·c)`, with the cube computed as `w·w·w/6`, `w = 1 − x`.
  - At `f = 0` there is no residual and the output is the naive triangle.
- **The rules.** As for the PolyBLEP sawtooth: `sample_rate` positive and finite, `num_samples`
  an integer of at least 0, `frequency` finite with `|f| ≤ fs/2`, `amplitude` and `phase`
  finite. Above `fs/4` the two corners' regions overlap and the residuals add.

## Consequences

- **Vectors.**
  - Expected values come from the rule in exact rationals, rounded once.
  - `E` and its slope are 0 at the region edges, so a rounding of `u` across an edge changes a
    sample by a rounding only.
  - The tolerance is `abs 1e-12, rel 1e-12`.
  - The Python tests check that the aliased energy is far below the naive triangle's.
