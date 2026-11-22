# ADR 0568: The Tsallis diversity of counts

Status: accepted, 2026-11-22.

## Context

The Tsallis entropy of order `q` of a set of shares is `(1 − Σ pᵢ^q)/(q − 1)`, the Shannon
entropy in the limit `q → 1`. `tsallis_entropy` (ADR 0355) bins samples into a histogram
first; this measure takes the record as abundances, like the Hill number. It is the
Patil–Taillie diversity (ADR 0565) at `β = q − 1`, named and parametrized as ecology
and physics use it.

## Decision

- **The API.**
  - Python: `tsallis_diversity(samples, order)` in `measurements`, giving a float.
  - C#: `Measurements.TsallisDiversity(ReadOnlySpan<double> samples, double order)`.
- **The shares.** `pᵢ = xᵢ/S`, `S` summed in record order; zero values are left out.
- **The form.**
  - `q = 1`: `−Σ pᵢ ln pᵢ`, terms in record order.
  - Otherwise `−(Σ pᵢ·expm1((q − 1) ln pᵢ))/(q − 1)`, the sum in record order. This is
    `(1 − Σ pᵢ^q)/(q − 1)` without subtracting two numbers near 1 when `q` is near 1.
- **The rules.** As for the Hill number: records as for the Gini coefficient, `order`
  finite and at least 0; otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator takes exact shares and evaluates `(1 − Σ pᵢ^q)/(q − 1)` in 60-digit
    decimal.
  - The tolerance is `abs 1e-12, rel 1e-12`.
