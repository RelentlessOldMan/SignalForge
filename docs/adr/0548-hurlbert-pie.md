# ADR 0548: Hurlbert's PIE

Status: accepted, 2026-11-21.

## Context

Hurlbert (1971) defines the probability of an interspecific encounter, PIE, as the chance
that two individuals drawn at random without replacement are of different kinds:
`N/(N − 1) · (1 − Σᵢ sᵢ²)`. It is the Gini–Simpson index (ADR 0529) with the finite
sample correction `N/(N − 1)`.

## Decision

- **The API.**
  - Python: `hurlbert_pie(samples)` in `measurements`, giving a float.
  - C#: `Measurements.HurlbertPie(ReadOnlySpan<double> samples)`.
- **The value.**
  - `PIE = N/(N − 1) · (1 − Σᵢ sᵢ²)`, `sᵢ = xᵢ/N` the shares, `N = Σᵢ xᵢ` and the squares
    added in record order; formed as `N/(N − 1) · (1 − Σ sᵢ²)`, left to right.
  - At least 0, and 0 when one value holds the total. For whole-number counts it is at most
    1, and equals `1 − Σ xᵢ(xᵢ − 1)/(N(N − 1))`; for other values it can exceed 1.
- **The rules.**
  - A real, finite, one-dimensional record, every value at least 0, with `N > 1` so the
    correction is defined (otherwise `invalid_argument`).

## Consequences

- One pass for the total, one for the squares; no sort.
- **Vectors.**
  - The generator forms the value exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
