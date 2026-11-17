# ADR 0237: Comb filter

Status: accepted, 2026-11-17.

## Context

A comb filter adds a delayed copy of the signal. The feedforward form puts notches at odd
multiples of `fs/(2D)` when `g > 0`. The feedback form puts resonant peaks at multiples of
`fs/D`. Combs are used for echo, flanging, harmonic notching and as the building block of
Schroeder reverberators.

## Decision

- **The API.**
  - Python: `comb_filter(samples, delay, gain, *, feedback=False)` in `dsp`.
  - C#: `Dsp.CombFilter(samples, delay, gain, feedback = false)`, for real or complex samples.
- **The value.** `D = delay`, `g = gain`, and `x` and `y` are zero before 0.
  - Feedforward: `y[n] = x[n] + g·x[n − D]`.
  - Feedback: `y[n] = x[n] + g·y[n − D]`.
  - The output has the input's length, with no tail.
- **The rules.**
  - `delay` must be an integer `≥ 1`.
  - `gain` must be finite. In the feedback form `|gain| < 1`, so the filter is stable.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - Feedforward cases come from the definition.
  - Feedback cases come from the impulse response `h[kD] = g^k`, which gives
    `y[n] = Σ_k g^k x[n − kD]`, without the recursion.
  - Both are computed in exact rational arithmetic, with gains that are binary fractions.
