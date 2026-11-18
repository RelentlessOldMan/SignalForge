# ADR 0296: Tape stop

Status: accepted, 2026-11-17.

## Context

A tape stop imitates a tape machine or turntable losing power: the playback slows to a halt,
and the pitch falls with it. Reading the input at a position that advances by a falling speed
gives the effect. The read uses the vibrato's linear interpolation (ADR 0271).

## Decision

- **The API.**
  - Python: `tape_stop(samples, start, length)` in `dsp`.
  - C#: `Dsp.TapeStop(samples, start, length)`.
  - `start` and `length` are integers in samples. Real samples only.
- **The value.**
  - Before and at `start`, the output is the input.
  - At `k = n − start` samples after it, the speed is `1 − k/L` with `L = length`. The read
    position is the running sum of the speeds:
    `p = start + Σ_{j=1}^{k} (1 − j/L) = start + (k − k(k+1)/(2L))`.
  - Both languages evaluate that closed form in that order, with `k(k+1)` as an exact double.
    No running sum is accumulated, so no error builds up.
  - For `1 ≤ k < L`: `i = ⌊p⌋`, `f = p − i`, `y = x[i]·(1 − f) + x[i+1]·f`. Since `p < n`,
    both samples exist.
  - From `k = L` on the tape has stopped, and the output is 0.
- **The rules.**
  - The samples must be real, finite and at least one.
  - `start` at least 0. A `start` past the end leaves the input as it is.
  - `length` at least 1. At 1 the output is silent right after `start`.

## Consequences

- **Vectors.**
  - Expected values come from the position and interpolation in exact rationals, rounded once.
  - The tolerance is `abs 1e-13, rel 1e-12`.
