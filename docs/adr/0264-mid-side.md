# ADR 0264: Mid/side coding

Status: accepted, 2026-11-17.

## Context

Stereo processing often works on the sum and difference of the two channels. Widening,
narrowing and centre-only compression all act on them. The encoder and decoder must invert each
other exactly, and both languages must scale them the same way. Some conventions scale by `1/√2`
and some by `1/2`. This one uses `1/2`, so the decoder is a plain sum and difference.

## Decision

- **The API.**
  - Python: `mid_side_encode(left, right)` returns `MidSide(mid, side)`, and
    `mid_side_decode(mid, side)` returns `LeftRight(left, right)`, both in `dsp`.
  - C#: `Dsp.MidSideEncode` returns the record `MidSide(Mid, Side)`, and `Dsp.MidSideDecode`
    returns `LeftRight(Left, Right)`.
  - Real samples only.
- **The value.**
  - Encode: `mid = (left + right)/2`, `side = (left − right)/2`.
  - Decode: `left = mid + side`, `right = mid − side`.
  - Each is evaluated in that order. Decoding an encoding gives back the input up to one
    rounding, or exactly when the sums are exact.
- **The rules.** Both inputs must be real, finite, non-empty and the same length.

## Consequences

- **Vectors.**
  - The inputs are binary fractions, so every expected value is exact.
  - The tolerance is `abs 1e-15`.
