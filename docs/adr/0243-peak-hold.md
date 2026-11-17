# ADR 0243: Peak hold

Status: accepted, 2026-11-17.

## Context

Level meters show a peak indicator. It jumps to each new peak, stays there for a while, and then
falls. The envelope follower (ADR 0238) starts falling at once.

## Decision

- **The API.**
  - Python: `peak_hold(samples, hold, release)` in `dsp`.
  - C#: `Dsp.PeakHold(samples, hold, release)`, for real or complex samples.
  - Both return real values.
- **The value.**
  - `r = |x[n]|`. The held value starts at `p = 0` and the counter at `c = 0`.
  - If `r ≥ p`: `p = r` and `c = 0`.
  - Otherwise, if `c < hold`: `c = c + 1`, and `p` is unchanged.
  - Otherwise: `p = release·p`, and if that is below `r`, `p = r`. `c` is not reset.
  - The output is `p` after each step.
  - So a peak lasts for `hold` samples after the one it arrived on, then falls by `release` per
    sample.
- **The rules.**
  - `hold` must be an integer `≥ 0`.
  - `release` must be finite, in `[0, 1)`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The definition runs in exact rationals, with binary-fraction `release` values. At a tie,
    both branches give the same value.
  - A single impulse of height `a` gives `a` for `hold + 1` samples, then `a·release^k`.
