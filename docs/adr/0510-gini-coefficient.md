# ADR 0510: The Gini coefficient

Status: accepted, 2026-11-20.

## Context

The Gini coefficient measures how unevenly a total is shared among `n` holders: the mean
absolute difference between two holders over twice the mean. Texts differ on whether the
mean absolute difference averages over all `n²` ordered pairs (the pair of a holder with
itself included) or over the `n(n − 1)` distinct pairs; the second scales the first by
`n/(n − 1)`.

## Decision

- **The API.**
  - Python: `gini_coefficient(samples)` in `measurements`, giving a float.
  - C#: `Measurements.GiniCoefficient(ReadOnlySpan<double> samples)`.
- **The value.**
  - `G = Σᵢ Σⱼ |xᵢ − xⱼ| / (2·n²·μ)`, over all `n²` ordered pairs: the population form,
    which equals the area between the Lorenz curve and the line of equality, doubled.
  - Computed on the sorted values `x₍₀₎ ≤ … ≤ x₍ₙ₋₁₎` as
    `Σₖ (2k − n + 1)·x₍ₖ₎ / (n·Σ x)`, one pass after the sort.
  - From 0, when every value is equal, to `1 − 1/n`, when one value holds the whole
    total. Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator sums `|xᵢ − xⱼ|` over every ordered pair of dyadic values exactly in
    rationals: the defining sum, not the sorted form.
  - The tolerance is `abs 1e-14, rel 1e-14`.
