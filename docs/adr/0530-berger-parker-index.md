# ADR 0530: The Berger–Parker index

Status: accepted, 2026-11-21.

## Context

Berger and Parker (1970) measure dominance by the share of the largest holder alone. Some
texts give its reciprocal as a diversity; here it is the share itself.

## Decision

- **The API.**
  - Python: `berger_parker_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.BergerParkerIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `max xᵢ / S`, `S` the total added in record order; one division.
  - From `1/n` (every value equal) to 1 (one value holds the total). The concentration
    ratio of ADR 0524 at `k = 1`.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- One pass for the total, one for the largest; no sort.
- **Vectors.**
  - The generator forms the share exactly in rationals from dyadic values.
  - The tolerance is `abs 1e-15, rel 1e-14`.
