# ADR 0299: Stutter

Status: accepted, 2026-11-17.

## Context

A stutter, or beat repeat, grabs a short slice of the input and plays it several times in a
row, then lets the input carry on. DJ and glitch effects use it. Like the reverse delay
(ADR 0298), it is a fixed reordering of the samples.

## Decision

- **The API.**
  - Python: `stutter(samples, start, length, repeats)` in `dsp`.
  - C#: `Dsp.Stutter(samples, start, length, repeats)`.
  - All three are integers, in samples except `repeats`. Real samples only.
- **The value.**
  - For `start ≤ n < start + repeats·length`, `y[n] = x[start + (n − start) mod length]`.
  - Elsewhere `y[n] = x[n]`.
  - The repeats replace the input, so the signal keeps its length and the part they cover is
    not heard. The input resumes at its own time, not where the slice ended.
  - A run past the end of the signal is cut off there. Every index it reads is at most `n`,
    so it always exists.
- **The rules.**
  - The samples must be real, finite and at least one.
  - `start` at least 0, `length` at least 1, `repeats` at least 0.
  - `repeats` of 0 or 1 leaves the input as it is.

## Consequences

- **Vectors.**
  - Expected values come from the index rule, transcribed in the stdlib. They are copies of
    input samples, so the tolerance is `abs 0, rel 0`.
