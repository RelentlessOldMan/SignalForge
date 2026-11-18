# ADR 0266: Bitcrusher

Status: accepted, 2026-11-17.

## Context

The lo-fi bitcrusher effect lowers the sample rate by holding samples, then lowers the
resolution by rounding to a coarse grid. Both parts already exist: the sample-and-hold
(ADR 0245) and the uniform quantizer (ADR 0247). The bitcrusher is one call with the
word-length convention fixed. For full scale `±1`, `b` bits give a step of `2^(1−b)` and
`2^b − 1` mid-tread levels, symmetric about zero, saturating at `±(1 − 2^(1−b))`.

## Decision

- **The API.**
  - Python: `bitcrush(samples, bits, *, hold=1)` in `dsp`.
  - C#: `Dsp.Bitcrush(samples, bits, hold = 1)`.
  - Real samples only.
- **The value.** `y = quantize(sample_and_hold(x, hold), 2^(1−bits), levels=2^bits − 1)`.
  - The hold has offset 0, so `y[n]` comes from `x[hold·⌊n/hold⌋]`.
  - The rounding is half to even.
  - With a power-of-two step, every output is exact.
- **The rules.**
  - `bits` must be an integer from 2 to 24.
  - `hold` must be an integer of at least 1.
  - The samples must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from exact rationals.
  - The tolerance is `abs 0`.
