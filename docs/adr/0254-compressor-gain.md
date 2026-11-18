# ADR 0254: Compressor gain computer

Status: accepted, 2026-11-17.

## Context

A dynamic-range compressor has two parts:

- a level detector, such as the envelope follower (ADR 0238) or moving RMS (ADR 0239), converted
  to dB;
- a static gain computer, which maps that level to a gain.

This ADR is the gain computer alone, in dB. It can be checked on its own, and it can be combined
with any detector. Its shape is the usual one. Below the threshold the gain is 0 dB. Above it, the
output rises `1/ratio` dB per input dB. An optional knee joins the two with a quadratic, so the
curve and its slope are continuous.

## Decision

- **The API.**
  - Python: `compressor_gain(level_db, threshold_db, ratio, *, knee_db=0.0)` in `dsp`.
  - C#: `Dsp.CompressorGain(levelDb, thresholdDb, ratio, kneeDb = 0)`.
  - It returns one gain in dB, `≤ 0`, per level. Add it to the level to get the output level.
- **The value.** Let `d = x − T`, `W = knee_db` and `s = 1/ratio − 1`.
  - `g = 0` if `2d < −W`.
  - `g = s·d` if `2d > W`.
  - Otherwise `g = s·(d + W/2)²/(2W)`. The two edges, `2|d| = W`, belong to this branch.
  - With `W = 0` the knee branch is the single point `d = 0`, where it gives `g = 0` and no
    division takes place.
  - The knee is evaluated as `q = d + W/2`, then `s·q·q/(2W)`, in that order in both languages.
- **The rules.**
  - `threshold_db` must be finite.
  - `ratio` must be finite and `≥ 1`. A ratio of 1 gives 0 dB everywhere.
  - `knee_db` must be finite and `≥ 0`.
  - The levels must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from the piecewise definition in exact rationals, with dyadic
    levels, thresholds and knees.
  - Ratios of 2, 4 and 8 make `s` exact. A ratio of 3 shows rounding, with a tolerance of about
    1e-14.
  - The cases include both knee edges, the threshold itself, and a hard knee.
