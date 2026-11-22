# ADR 0535: Bulla's evenness

Status: accepted, 2026-11-21.

## Context

Bulla (1994) measures evenness as the overlap between the shares and equal shares,
`O = Σ min(sᵢ, 1/n)`, then rescales it so that one holder gives 0. Some texts give the
overlap `O` itself (from `1/n` to 1); here it is the rescaled value. As for the other
evenness measures, `n` is the record length, zero shares included.

## Decision

- **The API.**
  - Python: `bulla_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.BullaEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = (O − 1/n)/(1 − 1/n)`, `O = Σᵢ min(sᵢ, 1/n)`, `sᵢ = xᵢ/S` the shares, `S` added
    in record order, the minima added in record order; `1/n` formed once.
  - From 0 (one value holds the total) to 1 (every value equal).
- **The rules.**
  - A real, finite, one-dimensional record of at least 2 values, every value at least 0,
    not all 0, as for Pielou's evenness.

## Consequences

- One pass for the total, one for the overlap; no sort.
- **Vectors.**
  - The generator forms the value exactly in rationals from dyadic values.
  - The tolerance is `abs 1e-15, rel 1e-14`.
