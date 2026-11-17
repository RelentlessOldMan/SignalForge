# ADR 0210: Reflection coefficients and prediction filters

Status: accepted, 2026-11-17. It completes the conversions between the AR model forms of
ADR 0149, ADR 0205 and ADR 0208.

## Context

Lattice filters, and coders that quantize reflection coefficients, need to move between the
reflection coefficients `k_1 … k_p` and the direct-form prediction-error filter `a`.

## Decision

- **The API.**
  - Python: `reflection_to_lpc(reflection)` and `lpc_to_reflection(coefficients)` in `dsp`.
  - C#: `Dsp.ReflectionToLpc` and `Dsp.LpcToReflection`, with real and complex overloads.
  - Real input gives real output.
- **The step-up.** It starts at `a = [1]`. For each `k_m` in order, it pads `a` with a zero and
  sets `a ← a + k_m·conj(reverse(a))`. This is the step of `levinson` and `burg`, so
  `a_m[m] = k_m`.
- **The step-down.** For `m = p … 1`:
  - `k_m = a_m[m]`;
  - `a_{m−1}[j] = (a_m[j] − k_m·conj a_m[m−j])/(1 − |k_m|²)`, for `j = 0 … m − 1`.
- **The rules.**
  - Every reflection coefficient, given or recovered, must have `|k| < 1`. The filters are
    then minimum phase.
  - The inputs must be finite and non-empty.
  - The filter needs `a_0 = 1` and order `≥ 1`.

## Consequences

- **Vectors.**
  - The order-2 and order-3 hand expansions are evaluated in exact fractions:
    - `a = [1, k_1 + k_2·conj k_1, k_2]`;
    - then `[1, a_1 + k_3·conj a_2, a_2 + k_3·conj a_1, k_3]`.
  - The `x = [1, 2, 3]` Burg values of ADR 0205 are used too.
  - Complex cases use the same expansions with `complex`.
