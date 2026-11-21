# ADR 0513: The coefficient of variation

Status: accepted, 2026-11-20.

## Context

The coefficient of variation is the standard deviation over the mean: a spread with no
unit. Texts differ on the standard deviation, over `n` (the population form) or over
`n − 1` (the sample form). Alongside the Gini coefficient, the Theil index and the Hoover
index (ADRs 0510–0512) it is an inequality measure, and those are all population forms.

## Decision

- **The API.**
  - Python: `coefficient_of_variation(samples)` in `measurements`, giving a float.
  - C#: `Measurements.CoefficientOfVariation(ReadOnlySpan<double> samples)`.
- **The value.**
  - `CV = σ/μ`, `σ = √((1/n)·Σ (xᵢ − μ)²)` the population standard deviation, over `n`,
    and `μ` the mean. The sample form is `CV·√(n/(n − 1))`.
  - At least 0; 0 when every value is equal. For values at least 0 it is at most
    `√(n − 1)`, when one value holds the whole total. Unchanged when every value is scaled
    by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value with a mean greater than 0.
    Values below 0 are allowed.

## Consequences

- The cost is two passes.
- **Vectors.**
  - The generator takes the mean and the population variance of dyadic values exactly in
    rationals and the square root in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
