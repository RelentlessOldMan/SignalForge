# ADR 0213: Spectral flatness of an AR model

Status: accepted, 2026-11-17. It uses the reflection coefficients of ADR 0205 and ADR 0210.

## Context

Spectral flatness, the geometric mean of a spectrum over its arithmetic mean, measures how
noise-like a signal is. For an AR model it has a closed form in the reflection coefficients,
so no spectrum has to be sampled.

## Decision

- **The API.**
  - Python: `ar_spectral_flatness(reflection)` in `dsp`, returning a `float`.
  - C#: `Dsp.ArSpectralFlatness`, with real and complex overloads, returning `double`.
- **The value.** It is `Π_m (1 − |k_m|²)`.
  - The model spectrum is `S = σ²/|A(e^{jω})|²`.
  - `A` is minimum phase, so the mean of `ln |A|²` over a period is 0 and the geometric mean of
    `S` is `σ²`.
  - The arithmetic mean of `S` is `r[0] = σ²/Π(1 − |k|²)`.
  - The gain `σ²` cancels, so it is not an argument. The value lies in `(0, 1]` and equals 1
    only for white noise (all `k = 0`).
- **The rules.** The reflection coefficients must be finite and non-empty, and every `|k| < 1`
  (ADR 0210's rule).

## Consequences

- **Vectors.**
  - The expected values are exact fraction products.
  - Each case is cross-checked in the generator by a stdlib numerical integral of
    `1/|A(e^{jω})|²` (geometric over arithmetic mean on a 4096-point grid), with `A` from the
    step-up recursion.
