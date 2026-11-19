# ADR 0372: Distance correlation

Status: accepted, 2026-11-18.

## Context

Székely, Rizzo and Bakirov (2007) defined the distance correlation. It is 0 exactly when the
two records are independent, so it detects relations that Pearson's and the rank
correlations (ADRs 0369–0371) miss, such as `y = x²`.

## Decision

- **The API.**
  - Python: `distance_correlation(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.DistanceCorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - The distances are `a_ij = |x_i − x_j|`.
  - The double-centred matrix is `A_ij = a_ij − ā_i· − ā_·j + ā_··`, from the row, column
    and grand means. The matrix is symmetric, so the row and column means are the same.
    `B` is built the same way from `y`.
  - `dCov² = (1/N²) Σ_ij A_ij B_ij` is the V-statistic, the paper's definition, not the
    bias-corrected U-statistic.
  - `dVar²(x) = (1/N²) Σ A_ij²`, and `dVar²(y)` the same from `B`.
  - `dCor = √(max(0, dCov²)/√(dVar²(x) · dVar²(y)))`. `dCov²` is never negative in exact
    arithmetic, so the `max` only guards against rounding.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - `N ≥ 2`.
  - Neither record has every value equal.

## Consequences

- The cost is `O(N²)` time and memory. The fast `O(N log N)` methods are not used.
- **Vectors.**
  - The generator takes every mean and sum exactly in rationals, then the two square roots
    in float.
  - The tolerance is `abs 1e-13, rel 1e-12`, since the means divide by `N` in float.
