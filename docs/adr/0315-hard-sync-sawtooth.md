# ADR 0315: Hard-synced sawtooth

Status: accepted, 2026-11-18.

## Context

Hard sync restarts a slave oscillator each time a master oscillator starts a cycle. The heard
pitch is the master's; sweeping the slave's frequency moves a resonant-sounding peak through
the spectrum. It is a staple of analog synthesizers. Nothing in `waveforms` resets one phase
from another.

## Decision

- **The API.**
  - Python: `hard_sync_sawtooth(sample_rate, num_samples, frequency, sync_frequency,
    amplitude=1)` in `waveforms`.
  - C#: `Waveforms.HardSyncSawtooth`, same arguments.
  - `frequency` is the slave's and `sync_frequency` the master's. Real output.
- **The value.**
  - `m = frac(sync_frequency·(n/fs))` is the master phase, built as the oscillators build `u`
    with phase 0.
  - The slave restarts at the exact moment the master wraps, not at the next sample. The
    time since that moment is `m / sync_frequency`, so the slave phase is
    `u = frac((frequency / sync_frequency)·m)`.
  - `y = A·(2·u − 1)`, the naive sawtooth of the slave phase.
  - With `frequency = sync_frequency` it is the naive sawtooth; it aliases like that one.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `sync_frequency` positive and finite, since a master that never wraps, or runs backwards,
    has no restarts.
  - `frequency` and `amplitude` finite. A negative slave frequency runs the slave backwards
    from each restart.

## Consequences

- **Vectors.**
  - Expected values come from the rule in exact rationals.
  - The cases keep each argument of `frac` at least `1e-9` from an integer unless it is
    exactly representable, so no rounding can move a sample across a jump.
  - The tolerance is `abs 1e-12, rel 1e-12`.
