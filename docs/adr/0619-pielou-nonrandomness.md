# ADR 0619: Pielou's index of non-randomness

Status: accepted, 2026-11-26.

## Context

Pielou (1959) measured how far a pattern of individuals in a plane departs from random
placement by the distance `u` from a point placed at random to the nearest individual. For
individuals placed at random with `ρ` individuals per unit area, `πρu²` is exponentially
distributed with mean 1, so the index `α = πρ Σu²/n` over `n` points is 1 at random, above 1
for a clumped pattern (the points fall in empty space) and below 1 for a regular one.

## Decision

- **The API.**
  - Python: `pielou_nonrandomness(point_distances, density)` in `measurements`, giving a
    float.
  - C#: `Measurements.PielouNonrandomness(ReadOnlySpan<double> pointDistances,
    double density)`.
- **The form.** With `t` the largest distance and `a = Σ(u/t)²` added in order, the value
  is `p²` with `p = (t √(a/n)) (√π √ρ)`: `p` is the square root of the value, so it
  overflows only when the value does, and `√ρ` of a subnormal density rounds once. (The
  first form, `q² (a/n)` with `q = t √(πρ)`, refused finite values: `πρ` overflows above
  about 5.7e307 and `q²` above 1.34e154; and `πρ` rounds for a subnormal ρ. Review fix,
  2026-11-26.) 0 when every distance is 0. The distances and the density are taken as
  given.
- **The rules.**
  - `point_distances` one-dimensional, real, finite, at least 0, not empty.
  - `density` finite and above 0.
  - A value that overflows is refused.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `Σu²/n` with fractions and π (by Machin's formula) with 60-digit
    decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`, for the rounding of the sum, the root and the
    square.
