# ADR 0250: Cubic soft clipper

Status: accepted, 2026-11-17.

## Context

Distortion models, limiters and saturating amplifier models need a smooth curve that rounds off
peaks instead of cutting them. The cubic `x − x³/3` is the simplest such curve. It is odd, and it
has a slope of 1 at 0 and a slope of 0 at `±1`. Beyond `±1` it is held at `±2/3`, so the curve
and its slope are both continuous there.

## Decision

- **The API.**
  - Python: `soft_clip(samples)` in `dsp`.
  - C#: `Dsp.SoftClip(samples)`.
  - Real samples only.
- **The value.**
  - `y = x − x·x·x/3` if `|x| < 1`, evaluated in that order.
  - `y = 2/3` if `x ≥ 1`, and `y = −2/3` if `x ≤ −1`, as the double nearest `2/3`. Evaluating
    the cubic at `±1` would round one ulp past it, so `±1` belongs to this branch.
  - It is memoryless.
  - To clip at another level or drive, scale the input before and the output after.
- **The rules.** The samples must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from the definition in exact rationals with binary-fraction
    samples, then rounded once to double.
  - The tolerance allows the one or two roundings of the float evaluation.
  - The cases include `±1`, which give `±2/3`, and samples beyond them.
