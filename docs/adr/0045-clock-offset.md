# ADR 0045: Sample clock offset

Status: accepted, 2026-11-13

## Context

A receiver's sample clock never quite matches the transmitter's. Over a long burst the symbol
timing drifts, which a block timing estimate cannot follow and a timing loop must. Testing that
needs a channel model that samples the signal at a slightly different rate.

## Decision

- `clock_offset(samples, ppm, *, half_width=16)`: the receiver takes a sample every
  `1 + ppm/1e6` input samples, read between samples by the `fractional_delay` kernel. The
  output is as long as the input lasts at that rate.
- The offset is in parts per million because that is how oscillators are specified; it is held
  to ±10 %, beyond which the call is a resampler, not a clock error.
- Only a constant offset: a wandering clock (jitter) is a later model.

## Consequences

- The kernel's error floor (about 2e-5 up to a quarter of the sample rate at the default
  width) applies.
- Vectors come from a stdlib generator with its own kernel and I0.
