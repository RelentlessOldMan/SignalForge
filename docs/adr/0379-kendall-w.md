# ADR 0379: Kendall's W

Status: accepted, 2026-11-19.

## Context

Kendall and Babington Smith (1939) measured how well `m` raters (or channels, or repeated
runs) agree on the order of the same `n` items: rank each rater's values, add the ranks per
item, and compare the spread of those sums with its largest possible value. It is 1 when
every rater gives the same order and 0 when the rank sums are all equal.

## Decision

- **The API.**
  - Python: `kendall_w(ratings)` in `measurements`, `ratings` a 2-D array with one row per
    rater and one column per item, giving a float.
  - C#: `Measurements.KendallW(double[][] ratings)`, rows of equal length.
- **The ranks.**
  - Each row is ranked on its own from 1, ties given the mean rank, as in ADR 0363.
- **The value.**
  - `R_j` is the sum of the ranks of item `j` over the raters, and
    `S = Σ_j (R_j − m(n + 1)/2)²`.
  - For each rater, `T = Σ (t³ − t)` over its groups of `t` tied values.
  - `W = 12 S/(m²(n³ − n) − m ΣT)`, from 0 to 1. Without ties this is Kendall's original
    `12 S/(m²(n³ − n))`.
  - The ranks are halves and `S` a multiple of `1/4`, so both are exact in float; the value
    is `12 S` divided by the integer denominator.
- **The rules.**
  - `ratings` real, two-dimensional and finite; `m ≥ 2` raters and `n ≥ 2` items.
  - The denominator positive: it is 0 only when every rater gives every item the same value.

## Consequences

- The cost is a sort per rater.
- Without ties, `W = ((m − 1) r̄ + 1)/m` with `r̄` the mean Spearman correlation (ADR 0369)
  over the pairs of raters; the tests check it.
- **Vectors.**
  - The generator ranks and sums exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
