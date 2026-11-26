# ADR 0609: Lloyd's mean crowding

Status: accepted, 2026-11-23.

## Context

Lloyd (1967) measured how crowded the individuals of a population are by the mean, over
the individuals, of the number of others in the same sampling unit. With `x_i` individuals
in unit `i`, each of them has `x_i − 1` others, so the mean crowding is
`m* = Σ x_i (x_i − 1)/Σ x_i`. It is 0 when no two individuals share a unit.

## Decision

- **The API.**
  - Python: `lloyd_mean_crowding(counts)` in `measurements`, giving a float.
  - C#: `Measurements.LloydMeanCrowding(ReadOnlySpan<double> counts)`.
- **The form.** With `t` the largest count, the value is `t · Σ(x_i/t)²/Σ(x_i/t) − 1`, the
  sums added in order: equal to the definition, and no sum can overflow. It is held at 0
  from below.
- **Review fix (2026-11-26).** The first form subtracted after summing (`s_2 − s_1/t`, or
  `t s_2/s_1 − 1`), which cancels when most counts are 1 and the index is small: for 1000
  ones and a 3 it was off by 4e-12 relative. The value now uses `c = Σ (x/t)((x − 1)/t)`,
  with `x − 1` formed before scaling, so each count of 1 adds an exact zero.
- **Definition, not estimator.** This is Lloyd's definition, `Σx(x − 1)/Σx`, which equals
  `m + (σ²/m − 1)` with `σ²` divided by `n`. Texts often quote Lloyd's estimator
  `x̄ + (s²/x̄ − 1)` with `s²` divided by `n − 1`; the two differ for few units (for
  `[1, 2, 3]`, 4/3 against 3/2). SignalForge gives the definition; a caller wanting the
  estimator can form it from the mean and the sample variance.
- **The rules.**
  - `counts` one-dimensional, real, finite, whole numbers at least 0, not empty, with a
    total above 0.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `Σ x(x − 1)/Σ x` with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums and the
    subtraction of 1.
