# ADR 0610: Lloyd's index of patchiness

Status: accepted, 2026-11-23.

## Context

Lloyd (1967) divided the mean crowding `m* = Σ x_i (x_i − 1)/Σ x_i` (ADR 0609) by the mean
count per unit `m = Σ x_i/n` to give the index of patchiness `m*/m`: how many times more
crowded an individual is than it would be if the population were spread evenly. For counts
drawn at random (Poisson) it is about 1; above 1 the population is clumped.

## Decision

- **The API.**
  - Python: `lloyd_patchiness(counts)` in `measurements`, giving a float.
  - C#: `Measurements.LloydPatchiness(ReadOnlySpan<double> counts)`.
- **The form.** With `t` the largest count and the sums `s_1 = Σ x_i/t`,
  `s_2 = Σ(x_i/t)²` added in order, the value is `(s_2/s_1 − 1/t) · n/s_1`: equal to
  `m*/m`, and nothing in it can overflow. It is held at 0 from below.
- **The rules.**
  - `counts` as for `lloyd_mean_crowding`: one-dimensional, real, finite, whole numbers at
    least 0, not empty, with a total above 0.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `m*` and `m` from the definitions with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums and the
    subtraction.
