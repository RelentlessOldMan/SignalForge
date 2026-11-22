# ADR 0567: Rényi evenness

Status: accepted, 2026-11-22.

## Context

Hill (1973) also measures evenness on the log scale: the Rényi diversity of order `q`
over its largest possible value, `E_q = ln D_q / ln K`, `K` the count of values above 0.
It is 1 for equal shares and tends to 0 as one kind dominates; `q = 0` always gives 1.

## Decision

- **The API.**
  - Python: `renyi_evenness(samples, order)` in `measurements`, giving a float.
  - C#: `Measurements.RenyiEvenness(ReadOnlySpan<double> samples, double order)`.
- **The form.** The Rényi diversity of counts of ADR 0566, with its switches, divided by
  `ln K`.
- **The rules.** As for the Hill number: records as for the Gini coefficient, `order`
  finite and at least 0. One kind leaves `0/0`, so at least two values must be above 0.
  Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator takes exact shares and evaluates `ln(Σ pᵢ^q)/((1 − q) ln K)` in
    60-digit decimal.
  - The tolerance is `abs 1e-12, rel 1e-12`.
