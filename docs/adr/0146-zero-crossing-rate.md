# ADR 0146: Zero-crossing rate

Status: accepted, 2026-11-16.

## Context

The zero-crossing rate counts how often a real signal changes sign. It is a cheap measure of
noisiness and a rough guide to dominant frequency. Definitions differ on several points:

- an exact 0, which some count as positive, some skip, and some count as half a crossing;
- the normalization, which is per sample pair, per sample, or per second;
- whether the rate is framed.

## Decision

- **The API.**
  - Python: `zero_crossing_rate(samples) -> float`.
  - C#: `Measurements.ZeroCrossingRate(ReadOnlySpan<double> samples)`.
- **The sign.** A sample counts as positive when `x ≥ 0`, and as negative otherwise. That
  includes `−0.0`, since `−0.0 ≥ 0`.
  - A signal that touches 0 from below and returns crosses twice.
  - A signal that touches 0 from above does not cross at all.
- **The value.** `rate = (number of n with sign(x[n]) ≠ sign(x[n+1])) / (N − 1)`, a fraction of
  the `N − 1` adjacent pairs, from 0 to 1. Multiply by the sample rate for crossings per second.
- **No frames.** Callers frame the signal themselves. A framed form can be added later without
  changing this one.
- **The rules.**
  - The samples are 1-D, real and finite, with at least two of them.
  - Python rejects complex input with `ValueError`. C# takes only real spans, so complex input
    has no vector.
  - Anything else is `invalid_argument`.

## Consequences

- **Exact zeros need care.** A sine sampled exactly at its zeros puts some samples at 0, which
  count as positive, so its count depends on the phase. Tests offset the phase.
- **Vectors.** These are counted by hand:
  - alternating samples.
  - constant-sign samples.
  - a zero after a positive.
  - a zero touched from below.
  - `−0.0`.
  - a mixed run.
  - the errors.
- **Tests.**
  - A sine with a phase offset crosses exactly twice per cycle.
  - Scaling the signal by a positive factor leaves the rate unchanged.
  - Python rejects complex input.
