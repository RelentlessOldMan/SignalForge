# ADR 0369: Spearman rank correlation

Status: accepted, 2026-11-18.

## Context

Spearman's rho (1904) measures how monotonically one record follows another, by
correlating their ranks. It does not assume a linear relation and is little moved by
outliers.

## Decision

- **The API.**
  - Python: `spearman_correlation(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.SpearmanCorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - Each record is ranked on its own, from 1. Equal values share the mean of the ranks they
    span, as in ADR 0363.
  - With `c = (N + 1)/2`, `rho = Σ (r_i − c)(s_i − c)/√(Σ (r_i − c)² · Σ (s_i − c)²)`. This
    is the Pearson correlation of the ranks. The shortcut `1 − 6Σd²/(N(N² − 1))` holds only
    without ties, so it is not used.
  - The ranks are multiples of 1/2, so for any practical `N` the three sums are exact in
    float. The product in the square root is taken first, then the square root, then the
    quotient.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - `N ≥ 2`.
  - Neither record has every value equal.

## Consequences

- **Vectors.**
  - The generator ranks each record and takes the sums in rationals. Then it takes the
    square root and the quotient in float.
  - The tolerance is `abs 1e-15, rel 1e-14`.
