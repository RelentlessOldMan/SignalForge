# ADR 0615: Fisher's index of dispersion statistic

Status: accepted, 2026-11-23.

## Context

Fisher, Thornton and Mackenzie (1922) tested whether counts in `n` sampling units are
Poisson with the statistic `D = Σ(x_i − m)²/m = (n − 1) s²/m`, with `m = Σx/n` the mean and
`s²` the sample variance (divided by `n − 1`). For Poisson counts it is close to
chi-square with `n − 1` degrees of freedom; larger values point to clumped counts, smaller
to even ones. It is 0 when the counts are all equal.

## Decision

- **The API.**
  - Python: `fisher_dispersion(counts)` in `measurements`, giving a float.
  - C#: `Measurements.FisherDispersion(ReadOnlySpan<double> counts)`.
- **The form.** With `t` the largest count and the sums `s_1 = Σ x_i/t`,
  `s_2 = Σ(x_i/t)²` added in order, the value is `t (n s_2/s_1 − s_1)`: equal to the
  definition. It is held at 0 from below. The factor of `t` is at most `n − 1`, so the value
  can overflow; then it is refused.
- **The rules.**
  - `counts` as for `david_moore_clumping`: one-dimensional, real, finite, whole numbers at
    least 0, at least two units, a total above 0.
  - A value that overflows is refused.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the mean and the sum of squared deviations from their definitions
    with fractions.
  - The tolerance is `abs 1e-14, rel 1e-13`, for the subtractions.
