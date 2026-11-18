# ADR 0251: Hard clipper

Status: accepted, 2026-11-17.

## Context

ADC overload, amplifier rail clipping and peak-limited transmitters all cut a signal off at a
level. For complex baseband the physical limit is on the magnitude, such as a PA's envelope, so a
complex sample is scaled back onto the circle and keeps its phase. It is not clamped part by part.

## Decision

- **The API.**
  - Python: `hard_clip(samples, limit)` in `dsp`.
  - C#: `Dsp.HardClip(samples, limit)`, real or complex in, the same kind out.
- **The value.**
  - Real: `y = min(max(x, −limit), limit)`.
  - Complex: `y = x` if `|x| ≤ limit`, else `y = x·(limit/|x|)`. `|x|` is `hypot` (`np.abs`,
    `Complex.Abs`).
  - `limit = 0` gives all zeros.
  - It is memoryless.
- **The rules.**
  - `limit` must be finite and `≥ 0`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - Real cases are exact: binary-fraction samples and limits, compared with zero tolerance.
  - Complex cases use 3-4-5 triangles, so `|x|` and `limit/|x|` are exact rationals. The
    expected values are rounded once from exact rationals, with a tolerance of a few ulps.
