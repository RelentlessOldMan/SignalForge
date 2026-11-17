# ADR 0245: Sample-and-hold

Status: accepted, 2026-11-17.

## Context

Models of ADC front ends, of decimation without filtering, and of staircase DAC outputs need a
signal that takes every `P`-th sample and holds it until the next one, at the original rate.
`upsample` and `interpolate` change the rate. This keeps the rate.

## Decision

- **The API.**
  - Python: `sample_and_hold(samples, period, *, offset=0)` in `dsp`.
  - C#: `Dsp.SampleAndHold(samples, period, offset = 0)`, real or complex in, the same kind out.
- **The value.**
  - The samples are taken at `n = offset + k·P`.
  - `y[n] = x[offset + P·⌊(n − offset)/P⌋]` for `n ≥ offset`.
  - `y[n] = 0` before the first sample is taken, starting from rest.
  - Every output is an exact copy of an input sample, or 0.
- **The rules.**
  - `period` must be an integer `≥ 1`.
  - `offset` must be an integer in `[0, period)`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values are the copied samples, written out by hand from the index rule. The
    tolerance is zero.
  - `period = 1` gives the input itself.
