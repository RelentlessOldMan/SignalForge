# ADR 0531: Heip's evenness

Status: accepted, 2026-11-21.

## Context

Heip (1974) scales the exponential of the Shannon entropy of the shares, the effective
number of holders, so that one holder gives 0 and equal holders give 1. Like Pielou's
evenness (ADR 0528) it depends on what `n` counts; here it is the record length, zero
shares included.

## Decision

- **The API.**
  - Python: `heip_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.HeipEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = (exp(H) − 1)/(n − 1)`, `H = −Σᵢ sᵢ ln sᵢ`, `sᵢ = xᵢ/S` the shares, `S` added in
    record order, `0·ln 0 = 0`, the terms added in record order.
  - From 0 (one value holds the total) to 1 (every value equal).
    `E = (HK(1) − 1)/(n − 1)`, `HK` the Hannah–Kay index (ADR 0527).
- **The rules.**
  - A real, finite, one-dimensional record of at least 2 values, every value at least 0,
    not all 0, as for Pielou's evenness.

## Consequences

- One pass for the total, one for the terms; no sort.
- **Vectors.**
  - The generator forms the shares exactly and the logarithms and exponential in 50-digit
    `decimal`; on equal shares the value is exact.
  - The tolerance is `abs 1e-14, rel 1e-13`, for `log` and `exp` in each language.
