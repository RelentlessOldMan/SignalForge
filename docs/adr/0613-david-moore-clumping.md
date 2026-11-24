# ADR 0613: David and Moore's index of clumping

Status: accepted, 2026-11-23.

## Context

David and Moore (1954) measured the clumping of counts of individuals in `n` sampling
units by how far the variance-to-mean ratio is above that of counts drawn at random
(Poisson), for which it is 1: `ICS = s²/m − 1`, with `m = Σx/n` the mean and `s²` the
sample variance (divided by `n − 1`). It is about 0 for counts at random, above 0 for
clumped counts and −1 when the counts are all equal.

## Decision

- **The API.**
  - Python: `david_moore_clumping(counts)` in `measurements`, giving a float.
  - C#: `Measurements.DavidMooreClumping(ReadOnlySpan<double> counts)`.
- **The form.** With `t` the largest count and the sums `s_1 = Σ x_i/t`,
  `s_2 = Σ(x_i/t)²` added in order, the value is `t (n s_2/s_1 − s_1)/(n − 1) − 1`: equal to
  the definition. As `s_2 ≤ s_1` and `s_1 ≥ 1`, the factor of `t` is at most 1, so nothing
  in it can overflow. It is held at −1 from below.
- **The rules.**
  - `counts` as for `lloyd_mean_crowding` (one-dimensional, real, finite, whole numbers at
    least 0, with a total above 0), with at least two units.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the mean and the sample variance from their definitions with
    fractions.
  - The tolerance is `abs 1e-14, rel 1e-13`, for the subtractions.
