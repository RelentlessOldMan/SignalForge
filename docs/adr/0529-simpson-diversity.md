# ADR 0529: The Gini–Simpson index

Status: accepted, 2026-11-21.

## Context

Simpson (1949) gives the chance that two members drawn at random belong to the same
holder; its complement, the Gini–Simpson index, is the chance that they differ. Texts
differ on drawing with or without replacement (the latter needs counts, not shares) and on
giving the complement or the reciprocal; here the draws are with replacement and the value
is the complement.

## Decision

- **The API.**
  - Python: `simpson_diversity(samples)` in `measurements`, giving a float.
  - C#: `Measurements.SimpsonDiversity(ReadOnlySpan<double> samples)`.
- **The value.**
  - `1 − Σᵢ sᵢ²`, `sᵢ = xᵢ/S` the shares, `S` added in record order, the squares added in
    record order and taken from 1 last. One less the Herfindahl index (ADR 0523).
  - From 0 (one value holds the total) to `1 − 1/n` (every value equal).
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- One pass for the total, one for the squares; no sort.
- **Vectors.**
  - The generator forms the index exactly in rationals from dyadic values.
  - The tolerance is `abs 1e-15, rel 1e-14`.
