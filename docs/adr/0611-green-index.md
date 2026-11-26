# ADR 0611: Green's index of dispersion

Status: accepted, 2026-11-23.

## Context

Green (1966) scaled the variance-to-mean ratio of counts of individuals in `n` sampling
units so that it does not grow with the number of individuals:
`G = (s²/m − 1)/(Σx − 1)`, with `m = Σx/n` the mean and `s²` the sample variance (divided
by `n − 1`). It is about 0 for counts drawn at random (Poisson), 1 when every individual is
in one unit, and `−1/(Σx − 1)` when the counts are all equal.

## Decision

- **The API.**
  - Python: `green_index(counts)` in `measurements`, giving a float.
  - C#: `Measurements.GreenIndex(ReadOnlySpan<double> counts)`.
- **The form.** With `t` the largest count and the sums `s_1 = Σ x_i/t`,
  `s_2 = Σ(x_i/t)²` added in order, `s²/m = t (n s_2/s_1 − s_1)/(n − 1)`, so
  `G = ((n s_2/s_1 − s_1)/(n − 1) − 1/t)/(s_1 − 1/t)`: equal to the definition, and nothing
  in it can overflow. It is held to [−1, 1].
- **Review fix (2026-11-26).** `n s_2/s_1 − s_1` is the same as `w n/s_1` with
  `w = Σ((x_i − m̂)/t)²` about `m̂ = t (s_1/n)`, but it subtracts two sums that agree to
  every digit when the mean is large next to the spread (`[1e9, 1e9 + 2e5]` was off by about 1e-8 relative). The value is now
  formed with `w`, added in a second pass; an error in `m̂` changes `w` only to second
  order. The form above is otherwise unchanged.
- **The rules.**
  - `counts` as for `lloyd_mean_crowding` (one-dimensional, real, finite, whole numbers at
    least 0), with at least two units and a total above 1.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the mean and the sample variance from the definitions with
    fractions.
  - The tolerance is `abs 1e-14, rel 1e-13`, for the subtractions.
