# ADR 0511: The Theil index

Status: accepted, 2026-11-20.

## Context

The Theil index is an inequality measure from information theory: the largest entropy of
`n` shares, `ln n`, less the entropy of the shares `x/Σ x`. Unlike the Gini coefficient
(ADR 0510) it splits exactly into a part within groups and a part between them.

## Decision

- **The API.**
  - Python: `theil_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.TheilIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `T = (1/n)·Σ (xᵢ/μ)·ln(xᵢ/μ)`, `μ` the mean, a term with `xᵢ = 0` taken as 0 (the
    limit of `r·ln r` as `r → 0`).
  - From 0, when every value is equal, to `ln n`, when one value holds the whole total.
    Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- The cost is one pass for the mean and one for the sum.
- **Vectors.**
  - The generator takes the mean of dyadic values exactly in rationals and each
    logarithm in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
