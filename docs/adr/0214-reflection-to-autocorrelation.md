# ADR 0214: Autocorrelation of an AR model

Status: accepted, 2026-11-17. It inverts `levinson` (ADR 0149) and completes the conversions of
ADR 0210.

## Context

The reflection coefficients and the zero-lag power fix an AR model. Its autocorrelation is
needed to compare models with measured lags, and to rebuild the Toeplitz matrix.

## Decision

- **The API.**
  - Python: `reflection_to_autocorrelation(reflection, power, lags)` in `dsp`.
  - C#: `Dsp.ReflectionToAutocorrelation`, with real and complex overloads.
  - Both return `r[0 … lags]`, so `lags + 1` values. The output is real when `k` is real.
- **The recursion.** It is Levinson's, solved for `r[m]`. Start with `r[0] = power`, `a = [1]`
  and `E = power`. Then, for `m = 1 … lags`:
  - let `s = Σ_{j=1}^{len(a)−1} a_j r[m−j]`;
  - if `m ≤ p`:
    - `r[m] = −k_m E − s`;
    - step `a` up with `k_m` (ADR 0210);
    - `E ← E(1 − |k_m|²)`;
  - otherwise, `r[m] = −s`. This is the AR extension.
- **The sign.** It follows `levinson`: `k_m = −(r[m] + Σ a_j r[m−j])/E`, so
  `levinson(reflection_to_autocorrelation(k, P, p), p)` gives back `k`, with error `P·Π(1 − |k|²)`.
- **The rules.**
  - The reflection coefficients must be finite and non-empty, and every `|k| < 1`.
  - `power` must be positive and finite.
  - `lags` must be an integer `≥ 0`.

## Consequences

- **Vectors.**
  - The expected values are the recursion evaluated in exact fractions.
  - AR(1) is checked against the closed form `r[m] = P(−k)^m`.
  - Every case is cross-checked in the generator by a stdlib Levinson run on the result, which
    must recover `k` and the error.
