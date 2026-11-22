# ADR 0564: Hill evenness

Status: accepted, 2026-11-21.

## Context

Jost (2010) measures evenness as the Hill number of order `q` over the number of kinds:
`E_q = D_q/K`, `K` the count of values above 0. It is 1 for equal shares and tends to
`1/K` as one kind dominates; `q = 0` always gives 1.

## Decision

- **The API.**
  - Python: `hill_evenness(samples, order)` in `measurements`, giving a float.
  - C#: `Measurements.HillEvenness(ReadOnlySpan<double> samples, double order)`.
- **The form.** The Hill number of ADR 0563, with its switches, divided by `K`.
- **The rules.** As for the Hill number: records as for the Gini coefficient, `order`
  finite and at least 0; otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator takes exact shares and evaluates `(Σ pᵢ^q)^{1/(1−q)}/K` in 60-digit
    decimal.
  - The tolerance is `abs 1e-12, rel 1e-12`.
