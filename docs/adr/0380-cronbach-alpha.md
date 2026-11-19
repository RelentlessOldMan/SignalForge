# ADR 0380: Cronbach's alpha

Status: accepted, 2026-11-19.

## Context

Cronbach (1951) measured the internal consistency of `k` measurements of the same subjects
(test items, sensors, repeated runs): how much of the variance of their sum comes from what
they share. It is 1 when every row is the same record up to an offset, and can be negative
when the rows disagree.

## Decision

- **The API.**
  - Python: `cronbach_alpha(scores)` in `measurements`, `scores` a 2-D array with one row per
    item and one column per subject, as for Kendall's W (ADR 0379), giving a float.
  - C#: `Measurements.CronbachAlpha(double[][] scores)`, rows of equal length.
- **The value.**
  - `σ_i²` is the sample variance (divisor `N − 1`) of row `i`, and `σ_t²` that of the
    column sums, the subject totals.
  - `α = k/(k − 1) · (1 − Σ σ_i² / σ_t²)`, at most 1.
  - Each variance is the sum of squared deviations from the row's mean over `N − 1`; the
    divisor cancels in the ratio but is kept so the parts are the usual variances.
- **The rules.**
  - `scores` real, two-dimensional and finite; `k ≥ 2` items and `N ≥ 2` subjects.
  - `σ_t² > 0`: the totals must not all be equal.

## Consequences

- The cost is one pass over the scores.
- Cronbach's alpha is the ICC(3,k) of the same table; that coefficient is not built.
- **Vectors.**
  - The generator forms the variances exactly in rationals.
  - The tolerance is `abs 1e-13, rel 1e-12`, for the rounding of the means and sums.
