# ADR 0563: The Hill number

Status: accepted, 2026-11-21.

## Context

Hill (1973) unified the diversity indices as the effective number of kinds of order `q`:
`D_q = (Σ pᵢ^q)^{1/(1−q)}` over the shares above 0, the limit `exp(−Σ pᵢ ln pᵢ)` at
`q = 1`. `q = 0` counts the kinds, `q = 2` is the inverse Simpson index, and large `q`
tends to `1/max pᵢ`.

## Decision

- **The API.**
  - Python: `hill_number(samples, order)` in `measurements`, giving a float.
  - C#: `Measurements.HillNumber(ReadOnlySpan<double> samples, double order)`.
- **The shares.** `pᵢ = xᵢ/S`, `S` summed in record order; zero values are left out.
- **The order.**
  - `q = 0`: the count of values above 0.
  - `q = 1`: `exp(−Σ pᵢ ln pᵢ)`, terms in record order.
  - `|q − 1| < 1/2`: `s = Σ pᵢ·expm1((q − 1) ln pᵢ)` in record order, which is
    `Σ pᵢ^q − 1` without cancellation, and `D = exp(log1p(s)/(1 − q))`. The plain form
    divides a rounding error by `1 − q` near 1.
  - Otherwise: `m = max pᵢ`, `t = Σ (pᵢ/m)^q` in record order, and
    `D = exp((q ln m + ln t)/(1 − q))`, so large orders do not underflow.
- **The rules.**
  - Records as for the Gini coefficient: real, finite, at least one value, every value at
    least 0, not all 0.
  - `order` finite and at least 0. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator takes exact shares and evaluates `(Σ pᵢ^q)^{1/(1−q)}` in 60-digit
    decimal, without either switch.
  - The tolerance is `abs 1e-12, rel 1e-12`.
