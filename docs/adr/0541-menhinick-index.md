# ADR 0541: Menhinick's index

Status: accepted, 2026-11-21.

## Context

Menhinick (1964) gives species richness relative to sample size as `k/√N`: the number of
kinds present over the square root of the number of individuals. Here the record holds
one count per kind; `k` counts the values above 0.

## Decision

- **The API.**
  - Python: `menhinick_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.MenhinickIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `D = k/√N`, `k` the number of values above 0, `N = Σᵢ xᵢ` added in record order.
  - Above 0. It depends on the scale of the values: scaling every value by `c` divides it
    by `√c`.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- One pass for the total, one for the count.
- **Vectors.**
  - The generator forms the total exactly and the square root in 50-digit `decimal`.
  - The tolerance is `abs 1e-15, rel 1e-14`, for one square root and one division.
