# ADR 0252: Wavefolder

Status: accepted, 2026-11-17.

## Context

Synthesis and distortion models fold a signal back into range when it overshoots, instead of
clamping it as ADR 0251 does. Each overshoot past `±limit` is reflected about that limit, again and
again, so a growing input sweeps up and down a triangle. The result keeps adding harmonics as the
drive rises, where a clipper only flattens.

## Decision

- **The API.**
  - Python: `wavefold(samples, limit)` in `dsp`.
  - C#: `Dsp.Wavefold(samples, limit)`.
  - Real samples only.
- **The value.** With `L = limit` and `P = 4L`:
  - `u = x + L`, then `t = u − P·⌊u/P⌋`, then `y = L − |t − 2L|`.
  - The operations are evaluated in that order in both languages, with no library modulo.
  - Inside `[−L, L]`, `y = x`. Past `L`, `y = 2L − x`, and so on.
  - The map is the triangle wave of `x` with period `4L` and peaks `±L`.
  - It is odd up to rounding, and memoryless.
- **The rules.**
  - `limit` must be finite and `> 0`.
  - The samples must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from repeated reflection, worked out by hand in exact rationals:
    reflect about `±L` until the value lies in `[−L, L]`.
  - This is a different route from the closed form the code uses.
  - Binary-fraction samples and limits make the closed form exact too, so the tolerance is zero.
