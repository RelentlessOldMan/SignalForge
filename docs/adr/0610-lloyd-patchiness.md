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
  - `counts` as for `lloyd_mean_crowding`: one-dimensional, real, finite, whole numbers at
    least 0, not empty, with a total above 0.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `m*` and `m` from the definitions with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums and the
    subtraction.
