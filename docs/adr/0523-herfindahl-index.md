# ADR 0523: The Herfindahl index

Status: accepted, 2026-11-21.

## Context

The Herfindahl (Herfindahl–Hirschman) index measures concentration: the sum of the squared
shares of a total. Texts differ in scale: shares as fractions give 0 to 1, shares as
percentages give 0 to 10 000, and a normalized form rescales `[1/n, 1]` to `[0, 1]`.

## Decision

- **The API.**
  - Python: `herfindahl_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.HerfindahlIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `H = Σᵢ (xᵢ/S)²`, `S = Σ x` added in record order, then the squared shares added in
    record order. Shares are fractions, so `H` runs from `1/n` (every value equal) to 1 (one
    value holds the total). No percentage scale and no normalized form.
  - `H = (1 + CV²)/n`, `CV` the population coefficient of variation (ADR 0513).
  - Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- The cost is two passes; no sort.
- **Vectors.**
  - The generator forms the squared shares exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
