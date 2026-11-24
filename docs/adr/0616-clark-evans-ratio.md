# ADR 0616: The Clark–Evans aggregation index

Status: accepted, 2026-11-23.

## Context

Clark and Evans (1954) measured how far a pattern of individuals in a plane departs from
random placement by the distance from each individual to its nearest neighbour. For
individuals placed at random (a Poisson process) with `ρ` individuals per unit area, the
mean of that distance is `r_E = 1/(2√ρ)`. The aggregation index is the observed mean over
it: `R = r̄/r_E = 2 r̄ √ρ`. It is 1 at random, below 1 for a clumped pattern (0 when every
individual has a neighbour at the same place) and at most about 2.1491, for a hexagonal
lattice.

## Decision

- **The API.**
  - Python: `clark_evans_ratio(distances, density)` in `measurements`, giving a float.
  - C#: `Measurements.ClarkEvansRatio(ReadOnlySpan<double> distances, double density)`.
- **The form.** With `t` the largest distance and `s_1 = Σ d_i/t` added in order, the mean
  is `t (s_1/n)`, and the value is `(t (s_1/n)) (2√ρ)`; 0 when every distance is 0. The
  distances and the density are taken as given: the function does not check that they come
  from one pattern, so the value is not held to the bounds above.
- **The rules.**
  - `distances` one-dimensional, real, finite, at least 0, not empty.
  - `density` finite and above 0.
  - A value that overflows is refused.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the mean with fractions and `√ρ` with 60-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sum and the root.
