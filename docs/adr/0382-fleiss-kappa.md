# ADR 0382: Fleiss' kappa

Status: accepted, 2026-11-19.

## Context

Fleiss (1971) measured how well a fixed number of raters agree when each puts every subject
into one of `q` categories, correcting for the agreement expected by chance from how often
each category is used overall. The raters need not be the same people for each subject.

## Decision

- **The API.**
  - Python: `fleiss_kappa(counts)` in `measurements`, giving a float. `counts` is 2-D, one
    row per subject and one column per category; entry `n_ij` is how many raters put
    subject `i` in category `j`.
  - C#: `Measurements.FleissKappa(double[][] counts)`, rows of equal length.
  - Counts, not labels: that is the form the measure is defined on and keeps the categories
    out of the API.
- **The value.**
  - `n` is the common row sum, the raters per subject, and `N` the number of subjects.
  - `p_j = Σ_i n_ij/(N n)`, the share of all ratings in category `j`, and
    `P̄_e = Σ_j p_j²`.
  - `P_i = (Σ_j n_ij² − n)/(n(n − 1))`, the agreeing share of rater pairs on subject `i`, and
    `P̄` its mean.
  - `κ = (P̄ − P̄_e)/(1 − P̄_e)`, at most 1.
  - The counts are whole numbers, so the sums are exact in float until they pass `2⁵³`.
- **The rules.**
  - `counts` real, two-dimensional, finite, whole and not negative; `N ≥ 1` subjects and
    `q ≥ 2` categories.
  - Every row sums to the same `n ≥ 2`.
  - `P̄_e < 1`: not every rating in one category.

## Consequences

- The cost is one pass over the counts.
- **Vectors.**
  - The generator forms `P̄` and `P̄_e` exactly in rationals. One case is Fleiss's example
    of 10 subjects, 14 raters and 5 categories, whose kappa of 0.210 the generator checks.
  - The tolerance is `abs 1e-14, rel 1e-13`.
