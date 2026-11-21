# ADR 0525: The Hall–Tideman index

Status: accepted, 2026-11-21.

## Context

The Hall–Tideman (1967) index, also given by Rosenbluth, measures concentration by
weighting each share by its rank from the largest. Texts rank from the largest or the
smallest, and from 1 or 0; the choice changes the value.

## Decision

- **The API.**
  - Python: `hall_tideman_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.HallTidemanIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `HT = 1/(2·Σ_r r·s₍ᵣ₎ − 1)`, `s₍ᵣ₎` the shares of the total ranked from the largest,
    `r` from 1 to `n`. Equal values tie without changing the sum.
  - Formed as `S/(2·A − S)`, `A = Σ_r r·x₍ᵣ₎` added from the largest (`r = 1`) down and
    `S` the total added in record order.
  - From `1/n` (every value equal) to 1 (one value holds the total).
    `HT = 1/(n·(1 − G))`, `G` the Gini coefficient of ADR 0510. Unchanged when every value
    is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator ranks dyadic shares from the largest and forms the index exactly in
    rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
