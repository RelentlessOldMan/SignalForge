# ADR 0549: Strong's dominance

Status: accepted, 2026-11-21.

## Context

Strong (2002) measures dominance from the Lorenz curve of the counts taken largest first:
the greatest vertical gap between the cumulative share of the `i` largest kinds and the
share `i/k` that equal kinds would give.

## Decision

- **The API.**
  - Python: `strong_dominance(samples)` in `measurements`, giving a float.
  - C#: `Measurements.StrongDominance(ReadOnlySpan<double> samples)`.
- **The value.**
  - `D = maxᵢ (bᵢ/N − i/k)` over `i = 1 … k`, `k` the number of values above 0, `bᵢ` the
    sum of the `i` largest values added largest first, `N = Σᵢ xᵢ` added in record order.
    Each term is formed as `bᵢ/N − i/k`; the running maximum starts at 0.
  - From 0 (every positive value equal, or a single one) to below 1. Zero values do not
    change it, and ties do not, as equal values give the same sums in any order.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- A sorted copy of the record: `O(n log n)`.
- **Vectors.**
  - The generator forms the value exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`; the running sum `bᵢ` is the only rounding
    that builds up.
