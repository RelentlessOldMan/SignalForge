# ADR 0512: The Hoover index

Status: accepted, 2026-11-20.

## Context

The Hoover index (the Robin Hood index) is the share of a total that would have to move
from the holders above the mean to those below it to make every holding equal: half the
mean absolute deviation over the mean. It is the largest vertical gap between the Lorenz
curve and the line of equality.

## Decision

- **The API.**
  - Python: `hoover_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.HooverIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `H = Σ |xᵢ − μ| / (2·Σ xᵢ)`, `μ` the mean.
  - From 0, when every value is equal, to `1 − 1/n`, when one value holds the whole
    total. Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient (ADR 0510).

## Consequences

- The cost is two passes.
- **Vectors.**
  - The generator sums the absolute deviations of dyadic values from their mean exactly
    in rationals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
