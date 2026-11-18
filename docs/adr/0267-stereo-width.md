# ADR 0267: Stereo width

Status: accepted, 2026-11-17.

## Context

Mid/side coding (ADR 0264) gives the usual width control: scale the side channel and decode.
A width of 0 folds the pair to mono, 1 leaves it as it is, and above 1 it widens. It is one
call over the encode and decode, with the evaluation order fixed so both languages round the
same way.

## Decision

- **The API.**
  - Python: `stereo_width(left, right, width)` in `dsp` returns `LeftRight`.
  - C#: `Dsp.StereoWidth(left, right, width)`.
  - Real samples only.
- **The value.**
  - `m = (left + right)/2`, `s = ((left − right)/2)·width`.
  - `left' = m + s`, `right' = m − s`.
  - Each is evaluated in that order.
  - At `width = 1` the output equals the input up to one rounding.
  - At `width = 0` both channels are `m`.
- **The rules.**
  - `width` must be finite and `≥ 0`.
  - Both inputs must be real, finite, non-empty and the same length.

## Consequences

- **Vectors.**
  - The inputs and widths are binary fractions, so every expected value is exact.
  - The tolerance is `abs 1e-15`.
