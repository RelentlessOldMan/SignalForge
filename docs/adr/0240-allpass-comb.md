# ADR 0240: Schroeder allpass section

Status: accepted, 2026-11-17.

## Context

Reverberators and diffusers chain allpass sections that have a long delay. Each section has a
flat magnitude response, and its impulse response is spread in time. The allpass designs of
ADR 0227 and before return coefficients for a single-sample delay. They do not filter a signal
through a delay line of `D` samples.

## Decision

- **The API.**
  - Python: `allpass_comb(samples, delay, gain)` in `dsp`.
  - C#: `Dsp.AllpassComb(samples, delay, gain)`, real or complex in, the same kind out.
- **The value.**
  - `y[n] = −g·x[n] + x[n−D] + g·y[n−D]`, with `x` and `y` zero before 0.
  - The terms are added in that order, left to right.
  - The transfer function is `H(z) = (−g + z^−D)/(1 − g z^−D)`, so `|H| = 1` at every frequency.
  - The impulse response is `h[0] = −g`, `h[kD] = (1 − g²)·g^(k−1)` for `k ≥ 1`, and 0
    elsewhere.
- **The rules.**
  - `delay` must be an integer `≥ 1`.
  - `gain` must be finite with `|g| < 1`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The generator convolves the input with that impulse response in exact rational arithmetic.
    It never runs the recursion.
  - The gains are binary fractions.
