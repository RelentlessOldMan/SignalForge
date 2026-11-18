# ADR 0297: Damped feedback comb

Status: accepted, 2026-11-17.

## Context

In a real room, high frequencies die away faster than low ones, because air and walls absorb
them. The plain feedback comb (ADR 0237) decays at every frequency alike, so reverbs built from
it ring metallically. Moorer's fix, used in Freeverb, puts a one-pole low-pass in the comb's
feedback path, so each trip round the loop loses more treble.

## Decision

- **The API.**
  - Python: `lowpass_feedback_comb(samples, delay, feedback, damping)` in `dsp`.
  - C#: `Dsp.LowpassFeedbackComb(samples, delay, feedback, damping)`.
  - Real samples only.
- **The value.**
  - `f[n] = (1 − d)·y[n − D] + d·f[n − 1]`, with `y[k] = 0` for `k < 0` and `f[−1] = 0`.
  - `y[n] = x[n] + g·f[n]`.
  - `D` is `delay`, `g` is `feedback` and `d` is `damping`.
  - Like the feedback comb, the output is not delayed: `y[0] = x[0]`. At `d = 0` it is the
    feedback comb of ADR 0237.
  - The response is `1/(1 − g·z^−D·(1 − d)/(1 − d·z^−1))`. At DC the low-pass passes 1, and
    at `fs/2` it passes `(1 − d)/(1 + d)`.
- **The rules.**
  - The samples must be real, finite and at least one.
  - `delay` an integer of at least 1.
  - `|feedback| < 1`. With `d` in [0, 1), the loop gain is then below 1 at every frequency,
    so the comb is stable.
  - `damping` in [0, 1).

## Consequences

- **Vectors.**
  - Expected values come from the recurrence in exact rationals, rounded once.
  - The tolerance is `abs 1e-14, rel 1e-12`.
- A reverb with damped combs is `schroeder_reverb` (ADR 0295) with the combs swapped. That is
  left to the caller.
