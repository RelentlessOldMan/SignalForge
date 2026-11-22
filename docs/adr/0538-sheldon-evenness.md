# ADR 0538: Sheldon's evenness

Status: accepted, 2026-11-21.

## Context

Sheldon (1969) gives evenness as the exponential of the Shannon entropy of the shares,
the effective number of holders, over the number of holders. As for the other evenness
measures, `n` here is the record length, zero shares included.

## Decision

- **The API.**
  - Python: `sheldon_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.SheldonEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = exp(H)/n`, `H = −Σᵢ sᵢ ln sᵢ`, `sᵢ = xᵢ/S` the shares, `S` added in record order,
    `0·ln 0 = 0`, the terms added in record order.
  - From `1/n` (one value holds the total) to 1 (every value equal).
    `E = HK(1)/n`, `HK` the Hannah–Kay index (ADR 0527).
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- One pass for the total, one for the terms; no sort.
- **Vectors.**
  - The generator forms the shares exactly and the logarithms and exponential in 50-digit
    `decimal`; on equal shares the value is exact.
  - The tolerance is `abs 1e-14, rel 1e-13`, for `log` and `exp` in each language.
