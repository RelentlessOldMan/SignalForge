# ADR 0617: The Clark–Evans test statistic

Status: accepted, 2026-11-23.

## Context

Clark and Evans (1954) tested the aggregation index `R = r̄/r_E` (ADR 0616) by the
standard normal deviate `z = (r̄ − r_E)/σ`. For `n` individuals placed at random with
density `ρ`, the nearest-neighbour distance has mean `r_E = 1/(2√ρ)` and variance
`(4 − π)/(4πρ)`, so the mean of `n` of them has standard error
`σ = √((4 − π)/(4πρn))`, which Clark and Evans wrote as `0.26136/√(nρ)`.

## Decision

- **The API.**
  - Python: `clark_evans_z(distances, density)` in `measurements`, giving a float.
  - C#: `Measurements.ClarkEvansZ(ReadOnlySpan<double> distances, double density)`.
- **The form.** Dividing through by `r_E`, `z = (R − 1) √(nπ/(4 − π))`, with `R` the
  aggregation index as `clark_evans_ratio` forms it. The constant is the exact one, not the
  rounded 0.26136, so values differ from Clark and Evans' tables in the fifth figure.
- **The rules.**
  - The arguments as for `clark_evans_ratio`: `distances` one-dimensional, real, finite, at
    least 0, not empty; `density` finite and above 0.
  - A value that overflows is refused.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the mean with fractions, and `√ρ`, π (by Machin's formula) and the
    root with 60-digit decimals.
  - The tolerance is `abs 1e-13, rel 1e-13`, for the subtraction of 1.
