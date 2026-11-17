# ADR 0242: Slew-rate limiter

Status: accepted, 2026-11-17.

## Context

Control signals, gain ramps and actuator models need the change per sample to be bounded, with
separate limits for rising and falling. A lowpass changes every value. A slew limiter only
changes the steps that are too large.

## Decision

- **The API.**
  - Python: `slew_limiter(samples, rise, fall)` in `dsp`.
  - C#: `Dsp.SlewLimiter(samples, rise, fall)`.
  - Real samples only.
- **The value.**
  - `y[−1] = 0`, starting from rest, like the other stateful filters.
  - `d = x[n] − y[n−1]`.
  - `y[n] = y[n−1] + rise` if `d > rise`, `y[n−1] − fall` if `d < −fall`, and `x[n]` otherwise.
    Within the limits the output is the input itself, with no rounding from `y + d`.
- **The rules.**
  - `rise` and `fall` must be finite and `> 0`.
  - The samples must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from the definition in exact rationals, with binary-fraction limits.
  - A step from 0 to `a` climbs as `min(a, (n + 1)·rise)`.
  - At a tie (`d = rise` or `d = −fall`), both branches give `x[n]` exactly. The generator
    asserts this.
