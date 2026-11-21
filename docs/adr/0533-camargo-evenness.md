# ADR 0533: Camargo's evenness

Status: accepted, 2026-11-21.

## Context

Camargo (1993) measures evenness from the gaps between every pair of shares, so that a
single dominant holder does not set the value alone. As for the other evenness measures,
`n` here is the record length, zero shares included.

## Decision

- **The API.**
  - Python: `camargo_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.CamargoEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = 1 − Σ_{i<j} |sᵢ − sⱼ| / n`, `sᵢ = xᵢ/S` the shares, `S` added in record order.
    The gaps are added over `i` in record order, then `j` from `i + 1`; divided by `n`
    and taken from 1 last.
  - From `1/n` (one value holds the total) to 1 (every value equal).
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- The cost is `n(n − 1)/2` gaps; the pairs are added directly so the two languages add
  them in the same order.
- **Vectors.**
  - The generator forms the value exactly in rationals from dyadic values.
  - The tolerance is `abs 1e-14, rel 1e-13`, for the many terms.
