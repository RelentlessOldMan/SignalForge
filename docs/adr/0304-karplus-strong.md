# ADR 0304: Karplus–Strong pluck

Status: accepted, 2026-11-17.

## Context

Karplus and Strong (1983) found that a burst of noise fed through a delay loop with a
two-point average in it sounds like a plucked string. The loop sets the pitch. The average is a
gentle low-pass, so every trip round it takes away more treble than bass, and the note dulls as
it fades, the way a string does. It is the damped comb (ADR 0297) with the simplest possible
filter in the loop.

## Decision

- **The API.**
  - Python: `karplus_strong(excitation, delay, length, decay)` in `dsp`.
  - C#: `Dsp.KarplusStrong(excitation, delay, length, decay)`.
  - Real samples only.
- **The value.**
  - `e` is the excitation, zero-padded to `length` samples.
  - `y[n] = e[n] + decay·((y[n − D] + y[n − D − 1])·0.5)`, with `y[k] = 0` for `k < 0`, in
    that order in both languages.
  - The loop delay is `D + 1/2` samples, so the fundamental is about `fs/(D + 1/2)`. The usual
    excitation is `D` or `D + 1` samples of noise.
- **The rules.**
  - The excitation must be real, finite, at least one sample and at most `length`.
  - `delay` an integer of at least 1.
  - `length` an integer of at least 1.
  - `decay` in [0, 1]. At 1 the loop loses nothing at DC, so a DC offset in the excitation
    never dies away; the averaging still takes the treble.

## Consequences

- **Vectors.**
  - Expected values come from the recurrence in exact rationals, rounded once.
  - The tolerance is `abs 1e-14, rel 1e-12`.
