# ADR 0256: Downward-expander gain computer

Status: accepted, 2026-11-17.

## Context

A downward expander is the mirror of a compressor (ADR 0254). Above the threshold it leaves the
level alone. Below it, it pushes quiet passages further down, `ratio` dB of output per input dB.
It is a gentler noise gate (ADR 0255). This ADR is its static gain computer in dB, shaped like
ADR 0254, with an optional quadratic knee.

## Decision

- **The API.**
  - Python: `expander_gain(level_db, threshold_db, ratio, *, knee_db=0.0)` in `dsp`.
  - C#: `Dsp.ExpanderGain(levelDb, thresholdDb, ratio, kneeDb = 0)`.
  - It returns one gain in dB, `≤ 0`, per level.
- **The value.** Let `d = x − T`, `W = knee_db` and `s = ratio − 1`.
  - `g = 0` if `2d > W`.
  - `g = s·d` if `2d < −W`.
  - Otherwise `q = d − W/2`, and `g = −(s·q·q/(2W))`, evaluated in that order. The two edges,
    `2|d| = W`, belong to this branch.
  - With `W = 0` the knee branch is the single point `d = 0`, where it gives `g = 0`.
  - The curve and its slope are continuous: the knee's slope runs from `s` at `d = −W/2` to `0`
    at `d = W/2`.
- **The rules.** The same as ADR 0254:
  - `threshold_db` must be finite.
  - `ratio` must be finite and `≥ 1`. A ratio of 1 gives 0 dB everywhere.
  - `knee_db` must be finite and `≥ 0`.
  - The levels must be real, finite and non-empty.

## Consequences

- **Vectors.** The expected values come from the piecewise definition in exact rationals, with
  dyadic levels and integer ratios, so every value is exact.
