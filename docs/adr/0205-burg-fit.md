# ADR 0205: Burg AR fit

Status: accepted, 2026-11-17. This ADR exposes the recursion of ADR 0204 on its own.

## Context

`burg_psd` (ADR 0204) fits an AR model and returns only its density. Linear predictive coding,
spectral line tracking and order selection all need the model itself. They want it in the
shape `levinson` already returns.

## Decision

- **The API.**
  - Python: `burg(samples, order)` in `dsp`.
  - C#: `Dsp.Burg`. It returns `Levinson` for real input and `ComplexLevinson` for complex input.
  - Both return a `Levinson(coefficients, reflection, error)`: the prediction-error filter
    (`a[0] = 1`, `order + 1` taps), the reflection coefficients `k_1 … k_p` and the final error.
  - Real samples give real arrays.
- **The recursion and its rules.** Both are exactly those of ADR 0204.
- **One copy.** `burg_psd` calls `burg` in each language, so the recursion lives in one place.

## Consequences

- **Vectors.**
  - The 3-sample case `x = [1, 2, 3]` is pinned to exact fractions.
  - Order 1, real and complex, is pinned to the closed form
    `k = −2 Σ x[n]·conj x[n−1] / Σ (|x[n]|² + |x[n−1]|²)`.
  - The rest come from the stdlib error recursion.
