# ADR 0305: Sawtooth, square and triangle oscillators

Status: accepted, 2026-11-17.

## Context

Subtractive synthesis starts from the classic waveforms: the sawtooth, which holds every
harmonic; the square, which holds the odd ones; and the triangle, whose odd harmonics fall as
`1/k²`. `tone` gives the sine. These are the naive forms, computed straight from the phase.
They alias above the Nyquist frequency, and band-limited forms (BLEP, additive) are a separate
item.

## Decision

- **The API.**
  - Python, in `waveforms`:
    - `sawtooth(sample_rate, num_samples, frequency, amplitude=1, phase=0)`;
    - `square(sample_rate, num_samples, frequency, duty=0.5, amplitude=1, phase=0)`;
    - `triangle(sample_rate, num_samples, frequency, amplitude=1, phase=0)`.
  - C#: `Waveforms.Sawtooth`, `Waveforms.Square` and `Waveforms.Triangle`, same arguments.
  - The output is real. Unlike `tone`, `phase` is in **cycles**, not radians, because the
    shapes are defined on a cycle.
- **The value.**
  - `t = f·(n/fs) + phase` and `u = t − floor(t)`, in [0, 1), in that order in both languages.
  - Sawtooth: `A·(2u − 1)`, rising from −A at the start of a cycle.
  - Square: `A` for `u < duty`, `−A` otherwise. `duty = 0` gives `−A` throughout and `duty = 1`
    gives `A`.
  - Triangle: `A·(4·|u − 1/2| − 1)`: `A` at the start of a cycle, `−A` at the half, so it
    lines up with `cos` the way `tone`'s real form does.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `frequency`, `amplitude` and `phase` finite. A negative frequency runs the phase backwards.
  - `duty` in [0, 1].

## Consequences

- **Vectors.**
  - Expected values come from the phase in exact rationals, rounded once. The cases keep the
    phase off the jumps, where a rounding could flip a sample from one side to the other.
  - The tolerance is `abs 1e-13, rel 1e-13`.
