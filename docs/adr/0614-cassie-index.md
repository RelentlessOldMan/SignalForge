# ADR 0614: Cassie's index

Status: accepted, 2026-11-23.

## Context

Cassie (1962) divided David and Moore's index of clumping `s²/m − 1` (ADR 0613) by the mean
count, `C = (s² − m)/m²`, with `m = Σx/n` the mean and `s²` the sample variance (divided by
`n − 1`). It is about 0 for counts drawn at random (Poisson); for negative binomial counts
it estimates `1/k`, the reciprocal of the clumping parameter. It is `−1/m` when the counts
are all equal, so it has no fixed lower bound.

## Decision

- **The API.**
  - Python: `cassie_index(counts)` in `measurements`, giving a float.
  - C#: `Measurements.CassieIndex(ReadOnlySpan<double> counts)`.
- **The form.** With `t` the largest count and the sums `s_1 = Σ x_i/t`,
  `s_2 = Σ(x_i/t)²` added in order, and `A = (n s_2/s_1 − s_1)/(n − 1)` as for David and
  Moore's index, the value is `(A − 1/t) · n/s_1`: equal to the definition, and nothing in
  it can overflow.
- **Review fix (2026-11-26).** `n s_2/s_1 − s_1` is the same as `w n/s_1` with
  `w = Σ((x_i − m̂)/t)²` about `m̂ = t (s_1/n)`, but it subtracts two sums that agree to
  every digit when the mean is large next to the spread (`[1e9, 1e9 + 2e5]` was off by about 1e-8 relative). The value is now
  formed with `w`, added in a second pass; an error in `m̂` changes `w` only to second
  order. The form above is otherwise unchanged.
- **The rules.**
  - `counts` as for `david_moore_clumping`: one-dimensional, real, finite, whole numbers at
    least 0, at least two units, a total above 0.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the mean and the sample variance from their definitions with
    fractions.
  - The tolerance is `abs 1e-14, rel 1e-13`, for the subtractions.
