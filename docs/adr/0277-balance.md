# ADR 0277: Stereo balance

Status: accepted, 2026-11-17.

## Context

A balance control moves a stereo image toward one side by turning the other side down. It is
not a panner: the panner (ADR 0265) splits one mono signal between two channels, while the
balance takes two channels and only attenuates. The side being favoured stays at unit gain, so
centring the control changes nothing.

## Decision

- **The API.**
  - Python: `balance(left, right, position)` in `dsp`, returning a `LeftRight` (ADR 0264).
  - C#: `Dsp.Balance(left, right, position)`, returning a `LeftRight`.
- **The value.** With `p = position`:
  - `gL = 1 − p` when `p > 0`, else `1`.
  - `gR = 1 + p` when `p < 0`, else `1`.
  - The output is `left·gL` and `right·gR`.
  - `p = −1` mutes the right, `p = 1` mutes the left.
- **The law is linear.** A constant-power balance would boost the near side at the centre, which
  breaks "centred changes nothing".
- **The rules.**
  - `position` must be finite and in `[−1, 1]`.
  - `left` and `right` must be real, finite, non-empty and the same length.

## Consequences

- **Vectors.** With dyadic positions every case is exact.
