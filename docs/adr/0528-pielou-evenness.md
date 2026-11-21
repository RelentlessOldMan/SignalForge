# ADR 0528: Pielou's evenness

Status: accepted, 2026-11-21.

## Context

Pielou (1966) scales the Shannon entropy of the shares by its largest possible value,
`ln n`, so that records of different lengths compare. Texts differ on the base of the
logarithm, which cancels, and on whether `n` counts the holders with a zero share; here it
does, as `n` is the record length.

## Decision

- **The API.**
  - Python: `pielou_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.PielouEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `J = −Σᵢ sᵢ ln sᵢ / ln n`, `sᵢ = xᵢ/S` the shares, `S` added in record order,
    `0·ln 0 = 0`, the terms added in record order. `n` is the record length, zero shares
    included.
  - From 0 (one value holds the total) to 1 (every value equal).
    `J = ln HK(1)/ln n`, `HK` the Hannah–Kay index (ADR 0527).
- **The rules.**
  - A real, finite, one-dimensional record of at least 2 values, every value at least 0,
    not all 0.

## Consequences

- One pass for the total, one for the terms; no sort.
- **Vectors.**
  - The generator forms the shares exactly and the logarithms in 50-digit `decimal`; on
    dyadic shares the value is exact.
  - The tolerance is `abs 1e-15, rel 1e-14`.
