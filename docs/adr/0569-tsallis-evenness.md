# ADR 0569: Tsallis evenness

Status: accepted, 2026-11-22.

## Context

The Tsallis diversity of counts of order `q` (ADR 0568) is largest for `K` equal shares,
`K` the count of values above 0, where it is `(1 − K^{1−q})/(q − 1)`, or `ln K` at `q = 1`.
Its ratio to that value is an evenness from 0 to 1, 1 for equal shares and at `q = 0`.

## Decision

- **The API.**
  - Python: `tsallis_evenness(samples, order)` in `measurements`, giving a float.
  - C#: `Measurements.TsallisEvenness(ReadOnlySpan<double> samples, double order)`.
- **The form.** The Tsallis diversity of counts over its maximum. The maximum is `ln K` at
  `q = 1`, else `−expm1((1 − q) ln K)/(q − 1)`, which keeps its digits near `q = 1`.
- **The rules.** As for the Hill number: records as for the Gini coefficient, `order`
  finite and at least 0. One kind leaves `0/0`, so at least two values must be above 0.
  Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator takes exact shares and evaluates `(1 − Σ pᵢ^q)/(1 − K^{1−q})`, or the
    Shannon entropy over `ln K` at `q = 1`, in 60-digit decimal.
  - The tolerance is `abs 1e-12, rel 1e-12`.
