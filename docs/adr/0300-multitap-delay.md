# ADR 0300: Multi-tap delay

Status: accepted, 2026-11-17.

## Context

A multi-tap delay reads one delay line at several points and sums the echoes with the input.
It gives rhythmic echo patterns, and early reflections in reverbs. It is an FIR filter with
sparse taps, so it is stated by its delays and gains rather than a dense tap vector.

## Decision

- **The API.**
  - Python: `multitap_delay(samples, delays, gains)` in `dsp`.
  - C#: `Dsp.MultitapDelay(samples, delays, gains)`.
  - `delays` is a list of integer delays in samples, `gains` one gain per delay. Real samples
    only.
- **The value.**
  - `y[n] = x[n] + Σ_k g_k·x[n − d_k]`, with `x[m] = 0` for `m < 0`.
  - The sum starts from `x[n]` and adds the taps in list order, one rounding per tap, in both
    languages.
  - Delays may repeat, and may be longer than the signal; such a tap adds nothing.
- **The rules.**
  - The samples must be real, finite and at least one.
  - 1 to 64 taps. Each delay at least 1; a gain on the dry signal is the caller's to apply.
  - One finite gain per delay.

## Consequences

- **Vectors.**
  - Expected values come from the sum in exact rationals, rounded once.
  - The tolerance is `abs 1e-14, rel 1e-13`, for the rounding of the float sum.
