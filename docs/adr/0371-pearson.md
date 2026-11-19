# ADR 0371: Pearson correlation

Status: accepted, 2026-11-18.

## Context

The Pearson product-moment correlation is the standard measure of linear association
between two records. SignalForge has had the rank correlations (ADRs 0369 and 0370) and the
cross-correlation sequence, but not the plain coefficient.

## Decision

- **The API.**
  - Python: `pearson_correlation(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.PearsonCorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - The means are `x̄ = (Σ x)/N` and `ȳ = (Σ y)/N`, in float.
  - `r = Σ (x − x̄)(y − ȳ)/√(Σ (x − x̄)² · Σ (y − ȳ)²)`.
  - The product of the two sums is formed in float, then the square root, then the quotient,
    as in ADR 0369.
  - The result is not clamped to [−1, 1]. Rounding can take it a few ulps past.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - `N ≥ 2`.
  - Neither record has every value equal.

## Consequences

- **Vectors.**
  - The vector samples are dyadic, with `N` a power of two, so the float means are exact
    (asserted).
  - The samples are kept small enough that every deviation product and sum is exact in float.
    So the generator takes the sums in rationals, and the square root and the quotient in
    float.
  - The tolerance is `abs 1e-15, rel 1e-14`.
