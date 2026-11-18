# ADR 0289: Octave-up effect

Status: accepted, 2026-11-17.

## Context

The classic analog octave-up pedal full-wave rectifies the signal. For a sine, `|sin|` has no
component at the input frequency: its lowest is at twice it, an octave up, plus a DC offset. A
DC blocker (ADR 0236) removes the offset, and the result is mixed with the dry signal as the
other effects mix.

## Decision

- **The API.**
  - Python: `octave_up(samples, pole, mix)` in `dsp`.
  - C#: `Dsp.OctaveUp(samples, pole, mix)`.
  - Real samples only. A complex signal has no single rectified form.
- **The value.**
  - `wet = dc_blocker(|x|, pole)`, run from rest.
  - `y = (1 − mix)·x + mix·wet`, the dry/wet blend of the other effects.
- **The rules.**
  - The samples must be real, finite and at least one.
  - The DC blocker's rule for `pole`: in [0, 1).
  - `mix` in [0, 1].

## Consequences

- **Vectors.**
  - Expected values come from the ADR 0236 recurrence on the rectified samples in exact
    rationals, rounded once, then blended in stdlib floats.
  - The tolerance is `abs 1e-15, rel 1e-12`.
- The rectifier's harmonics alias above a quarter of the sample rate. Callers who need that
  clean should oversample first.
