# ADR 0532: Simpson's evenness

Status: accepted, 2026-11-21.

## Context

Simpson's evenness scales the inverse Simpson index, the numbers equivalent `1/Σ sᵢ²`, by
the record length, so that equal holders give 1. As for the other evenness measures,
`n` here is the record length, zero shares included.

## Decision

- **The API.**
  - Python: `simpson_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.SimpsonEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = 1/(n·Σᵢ sᵢ²)`, `sᵢ = xᵢ/S` the shares, `S` added in record order, the squares
    added in record order.
  - From `1/n` (one value holds the total) to 1 (every value equal).
    `E = 1/(n·H) = HK(2)/n`, `H` the Herfindahl index (ADR 0523), `HK` the Hannah–Kay
    index (ADR 0527).
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- One pass for the total, one for the squares; no sort.
- **Vectors.**
  - The generator forms the value exactly in rationals from dyadic values.
  - The tolerance is `abs 1e-15, rel 1e-14`.
