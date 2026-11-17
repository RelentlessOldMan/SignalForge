# ADR 0246: Dead zone

Status: accepted, 2026-11-17.

## Context

Control loops, sensor models and noise cleaners use a dead zone. Small inputs map to 0, and
larger ones are shifted toward 0 by the width of the zone, so the output has no jump at the edge
of the zone. This is the soft threshold of wavelet denoising.

## Decision

- **The API.**
  - Python: `dead_zone(samples, width)` in `dsp`.
  - C#: `Dsp.DeadZone(samples, width)`.
  - Real samples only.
- **The value.**
  - `y = 0` if `|x| ≤ width`.
  - `y = x − width` if `x > width`.
  - `y = x + width` if `x < −width`.
  - It is memoryless, and the output is continuous in `x`.
  - `width = 0` gives the input itself.
- **The rules.**
  - `width` must be finite and `≥ 0`.
  - The samples must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from the definition in exact rationals, with binary-fraction
    samples and widths.
  - The cases include samples exactly at `±width`, which give 0.
