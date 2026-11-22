# ADR 0565: The Patil–Taillie diversity

Status: accepted, 2026-11-21.

## Context

Patil and Taillie (1982) give a one-parameter family of diversities,
`Δ_β = (1 − Σ pᵢ^{β+1})/β` over the shares above 0, `β ≥ −1`. `β = −1` gives the count of
kinds less 1, the limit `β → 0` the Shannon entropy in nats, and `β = 1` the Gini–Simpson
index.

## Decision

- **The API.**
  - Python: `patil_taillie_diversity(samples, beta)` in `measurements`, giving a float.
  - C#: `Measurements.PatilTaillieDiversity(ReadOnlySpan<double> samples, double beta)`.
- **The shares.** `pᵢ = xᵢ/S`, `S` summed in record order; zero values are left out.
- **The form.**
  - `β = 0`: `−Σ pᵢ ln pᵢ`, terms in record order.
  - Otherwise `−Σ pᵢ·expm1(β ln pᵢ)/β`, the sum in record order, then divided by `β`.
    `Σ pᵢ^{β+1} − 1 = Σ pᵢ(pᵢ^β − 1)`, so this avoids subtracting two numbers near 1 when
    `β` is small.
- **The rules.**
  - Records as for the Gini coefficient: real, finite, at least one value, every value at
    least 0, not all 0.
  - `beta` finite and at least −1. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator takes exact shares and evaluates `(1 − Σ pᵢ^{β+1})/β` in 60-digit
    decimal.
  - The tolerance is `abs 1e-12, rel 1e-12`.
