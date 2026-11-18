# ADR 0294: Slicer

Status: accepted, 2026-11-17.

## Context

A slicer, or trance gate, chops a sustained sound into a rhythm. It passes the signal for the
first part of each cycle and mutes it for the rest. It is the tremolo (ADR 0261) with a square
gain instead of a raised cosine.

## Decision

- **The API.**
  - Python: `slicer(samples, rate, duty, sample_rate)` in `dsp`.
  - C#: `Dsp.Slicer(samples, rate, duty, sampleRate)`.
  - Real samples only.
- **The value.**
  - The cycle position is `p = t − floor(t)` with `t = rate·(n/fs)`. Both languages compute
    it in that order, so they agree at the edges.
  - The gain is 1 where `p < duty` and 0 otherwise. `y[n] = x[n]·gain[n]`.
  - The cycle starts open at `n = 0`.
  - The edges are hard. A caller who wants no clicks smooths the gain or follows with a
    low-pass.
- **The rules.**
  - The samples must be real, finite and at least one.
  - `rate` finite and at least 0. At 0 the gate stays at the start of its cycle.
  - `duty` in [0, 1]. At 0 the output is silent; at 1 it is the input.
  - `fs` finite and positive.

## Consequences

- **Vectors.**
  - Expected values come from the rule, at rates and sample rates whose positions are exact
    binary fractions, so no case sits on a rounding edge.
  - The tolerance is `abs 0, rel 0`.
