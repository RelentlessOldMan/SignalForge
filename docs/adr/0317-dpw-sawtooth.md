# ADR 0317: DPW sawtooth

Status: accepted, 2026-11-18.

## Context

The differentiated parabolic waveform (Välimäki, 2005) is another cheap alias-reduced
sawtooth. Square the naive sawtooth `x = 2u − 1` to get a parabola, which has no jump and so
much weaker aliased harmonics. Then differentiate it back with a first difference: the
derivative of `x²` is `2x·dx/dt = 4·f·x`, so the scaled difference gives back a sawtooth. The
difference also acts as a gentle highpass that leaves the aliases a little lower again. It
costs a square and a subtraction a sample, against the PolyBLEP form's branch (ADR 0310).

## Decision

- **The API.**
  - Python: `dpw_sawtooth(sample_rate, num_samples, frequency, amplitude=1, phase=0)` in
    `waveforms`.
  - C#: `Waveforms.DpwSawtooth`, same arguments.
  - Real output, `phase` in cycles.
- **The value.**
  - `u[n]` is the oscillators' phase, built the same way for `n = −1`, so the first sample has
    a true predecessor and no start-up transient.
  - `x[n] = 2·u[n] − 1`.
  - `y[n] = A·((x[n]·x[n] − x[n−1]·x[n−1])·(fs/(4·f)))`.
  - At `f = 0` the output is the naive `A·x[n]`, the limit as `f → 0`.
  - The sign of `f` cancels between the difference and the scale, so a negative frequency
    gives the falling sawtooth.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `frequency` finite with `|f| ≤ fs/2`, as for the PolyBLEP oscillators. `amplitude` and
    `phase` finite.
- **Precision.** The difference cancels. Its relative rounding error grows like `fs/|f|`, about
  `1e-12` at `f = fs/10⁴`. That is fine for audio, but a very low pitch should use the
  PolyBLEP form.

## Consequences

- **Vectors.**
  - Expected values come from the rule in exact rationals, rounded once.
  - The parabola has no jump, so a rounding of `u` across the wrap changes a sample by a
    rounding times `fs/|f|` only. The cases keep `|f|/fs` at least `1/200`.
  - The tolerance is `abs 1e-11, rel 1e-11`.
  - The Python tests check that the aliased energy is below the naive sawtooth's.
