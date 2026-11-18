# ADR 0343: Weighted permutation entropy

Status: accepted, 2026-11-18.

## Context

Permutation entropy (ADR 0325) counts every window the same, so a window of small noise
between large events weighs as much as an event. Fadlallah, Chen, Keil and Príncipe (2013)
weighted each window by its variance. That keeps the amplitude information and makes the
measure less sensitive to noise in quiet stretches.

## Decision

- **The API.**
  - Python: `weighted_permutation_entropy(samples, order, delay=1)` in `measurements`,
    giving a float.
  - C#: `Measurements.WeightedPermutationEntropy(ReadOnlySpan<double> samples, int order,
    int delay = 1)`.
- **The value.**
  - The windows and their ordinal patterns are those of permutation entropy (ADR 0325),
    with ties broken by index.
  - Window `j` has weight `w_j = (1/order)·Σ_l (x_{j+l·delay} − mean_j)²`, its population
    variance.
  - `p(π) = Σ_{j with pattern π} w_j / Σ_j w_j`.
  - The value is `−Σ p·ln p / ln(order!)` over the patterns with `p > 0`, from 0 to 1.
- **The rules.**
  - Those of permutation entropy: `order` from 2 to 8, `delay` at least 1, at least one
    window, and the samples real and finite.
  - At least one window must vary, so that `Σ w > 0`.

## Consequences

- **Vectors.**
  - The generator finds each pattern by sorting `(value, index)` pairs. It takes the
    weights and the `p` exactly in rationals, and the logarithms in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
