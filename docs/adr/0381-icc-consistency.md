# ADR 0381: The intraclass correlation ICC(3,1)

Status: accepted, 2026-11-19.

## Context

Shrout and Fleiss (1979) set out six intraclass correlations for `k` raters (or instruments,
or channels) measuring the same `n` subjects. ICC(3,1) is the two-way mixed model for
consistency of a single rating: each rater may carry its own offset, and the question is how
much of what is left varies between subjects rather than as error.

## Decision

- **The API.**
  - Python: `icc_consistency(ratings)` in `measurements`, `ratings` a 2-D array with one row
    per rater and one column per subject, as for Kendall's W (ADR 0379), giving a float.
  - C#: `Measurements.IccConsistency(double[][] ratings)`, rows of equal length.
  - Only ICC(3,1) is built. The name says what it measures; the others would get names of
    their own.
- **The value.**
  - `x̄` is the grand mean, `r_i` the mean of row `i` and `c_j` of column `j`.
  - `SS_S = k Σ_j (c_j − x̄)²` between subjects, and `SS_E = Σ (x_ij − r_i − c_j + x̄)²` the
    residual, formed from the residuals directly rather than by subtraction.
  - `MS_S = SS_S/(n − 1)`, `MS_E = SS_E/((n − 1)(k − 1))`.
  - `ICC = (MS_S − MS_E)/(MS_S + (k − 1) MS_E)`, from `−1/(k − 1)` to 1.
- **The rules.**
  - `ratings` real, two-dimensional and finite; `k ≥ 2` raters and `n ≥ 2` subjects.
  - The denominator positive: it is 0 only when every column is the same after the rater
    offsets are removed.

## Consequences

- The cost is one pass over the ratings for the means and one for the sums of squares.
- Cronbach's alpha (ADR 0380) of the same table is ICC(3,k),
  `k ICC/(1 + (k − 1) ICC)`; the tests check it.
- **Vectors.**
  - The generator forms the sums of squares exactly in rationals. One case is the example
    table of Shrout and Fleiss, whose published ICC(3,1) of 0.71 the generator checks.
  - The tolerance is `abs 1e-13, rel 1e-12`.
