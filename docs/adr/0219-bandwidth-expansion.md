# ADR 0219: Bandwidth expansion

Status: accepted, 2026-11-17. It works on the prediction-error filters of ADR 0149 and ADR 0205.

## Context

Speech coders widen the formant bandwidths of an LPC model before quantizing or synthesizing
it. This avoids sharp spectral peaks and improves the numerical margin to instability.

## Decision

- **The API.**
  - Python: `bandwidth_expansion(coefficients, factor)` in `dsp`.
  - C#: `Dsp.BandwidthExpansion`, with real and complex overloads.
  - The output has the type of the input.
- **The value.** It is `a_j ← a_j·γʲ`, which is `A(z/γ)`. Every root moves from `p` to `γp`, so
  every pole radius shrinks by `γ` and the phase is unchanged.
- **The rules.**
  - The coefficients must be finite and non-empty. Any `a_0` is allowed, because the map is
    defined on any polynomial.
  - `factor` must be real with `0 < γ ≤ 1`, so a minimum-phase filter stays minimum phase.

## Consequences

- **Vectors.**
  - The expected values are exact fraction powers.
  - An order-1 filter `[1, −p]` must become `[1, −γp]`, with its pole at `γp`.
  - A complex case is included.
