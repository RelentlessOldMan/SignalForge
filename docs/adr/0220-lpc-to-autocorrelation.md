# ADR 0220: Autocorrelation of a prediction-error filter

Status: accepted, 2026-11-17. It composes ADR 0210's step-down with ADR 0214.

## Context

Callers usually hold an AR model as `a` and `σ²`, not as `k` and `r[0]`. ADR 0217 already
needed this conversion inside the Itakura-Saito distance.

## Decision

- **The API.**
  - Python: `lpc_to_autocorrelation(coefficients, error, lags)` in `dsp`.
  - C#: `Dsp.LpcToAutocorrelation`, with real and complex overloads.
  - Both return `r[0 … lags]`, so `lags + 1` values. The output has the type of the input.
- **The value.**
  - `k = lpc_to_reflection(a)`, then `r = reflection_to_autocorrelation(k, σ²/Π(1 − |k|²), lags)`.
  - For order 0 (`a = [1]`), it is `[σ², 0, …]`.
  - `levinson(r, p)` gives back `a` and `σ²`.
  - The Itakura-Saito distance now calls this function, with no change in value.
- **The rules.**
  - The filter must be finite and non-empty, with `a[0] = 1`, and minimum phase.
  - `error` must be positive and finite.
  - `lags` must be an integer `≥ 0`.

## Consequences

- **Vectors.**
  - The expected values are the step-down and the ADR 0214 recursion evaluated in exact
    fractions.
  - Each case is cross-checked in the generator against the normal equations:
    - `Σ_j a_j r[m − j] = 0` for `1 ≤ m ≤ lags`;
    - `Σ_j a_j r[−j] = σ²`, with `r[−j] = conj r[j]`.
