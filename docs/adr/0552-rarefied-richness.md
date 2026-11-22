# ADR 0552: The rarefied richness

Status: accepted, 2026-11-21.

## Context

Hurlbert (1971) and Sanders (1968) compare richness across samples of different sizes by
the number of kinds expected in a smaller subsample. For `n` individuals drawn without
replacement from `N`, a kind with `xᵢ` individuals is missed with probability
`C(N − xᵢ, n)/C(N, n)`, so the expected count of kinds is `Σᵢ (1 − C(N − xᵢ, n)/C(N, n))`.

## Decision

- **The API.**
  - Python: `rarefied_richness(samples, size)` in `measurements`, giving a float.
  - C#: `Measurements.RarefiedRichness(ReadOnlySpan<double> samples, int size)`.
- **The value.**
  - `E = Σᵢ (1 − qᵢ)` over the values above 0, in record order, with the miss probability
    `qᵢ = C(N − xᵢ, n)/C(N, n) = Πⱼ (N − n − j)/(N − j)` for `j = 0 … xᵢ − 1`, the product
    taken in that order and stopped once it reaches 0 (when `N − n − j = 0`).
  - From 1 (at `n = 1`) to `k`, the count of values above 0 (at `n = N`); it rises with `n`.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.
  - `size` an integer from 1 to `N` (otherwise `invalid_argument`); in Python a float, even
    a whole one, or a bool is rejected.

## Consequences

- At most `N` factors in all, so at most 10 000 000 steps.
- **Vectors.**
  - The generator forms each `C(N − xᵢ, n)/C(N, n)` exactly from binomial coefficients.
  - The tolerance is `abs 1e-12, rel 1e-12`: each product rounds once per factor.
