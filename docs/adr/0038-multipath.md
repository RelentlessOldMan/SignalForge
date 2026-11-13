# ADR 0038: Multipath

Status: accepted, 2026-11-13

## Context

A static multipath channel is a sparse FIR filter: a few echoes, each a delay and a complex
gain. Implementations differ on three things: whether delays are integer samples or fractional
(which needs an interpolator), whether the output keeps the convolution tail, and whether gains
are normalized to unit total power.

## Decision

- `multipath(samples, delays, gains)`: integer sample delays `≥ 0`, complex gains used as given
  (no normalization), output as long as the input with the tail dropped.
- The same length as the input keeps it a drop-in channel stage next to `awgn`,
  `frequency_offset` and the impairments, all of which return as many samples as they take.
- Gains are not normalized, because a caller modelling a profile (or a loss) means the numbers
  given; a caller who wants unit power divides by `√Σ|g|²` first.

## Consequences

- Fractional delays and time-varying (fading) paths are later models; this one can be built on
  by both (a fractional delay is an interpolating filter per path).
- Vectors are by hand: impulse responses, repeated delays, a delay past the end.
