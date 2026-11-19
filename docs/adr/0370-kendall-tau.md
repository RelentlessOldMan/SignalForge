# ADR 0370: Kendall's tau-b

Status: accepted, 2026-11-18.

## Context

Kendall (1938, ties 1945) measures the agreement in order between two records by counting
the pairs that rise together and the pairs that move apart. Tau-b is the form corrected for
ties, and it is what most libraries return by default. It goes with Spearman's rho
(ADR 0369).

## Decision

- **The API.**
  - Python: `kendall_tau(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.KendallTau(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - `n_c − n_d = Σ_{i<j} sign(x_j − x_i) · sign(y_j − y_i)`, an integer.
  - `n₀ = N(N − 1)/2`.
  - `n₁ = Σ t(t − 1)/2` over the groups of `t` equal values in `x`, and `n₂` the same for `y`.
  - `tau = (n_c − n_d)/√((n₀ − n₁)(n₀ − n₂))`. The counts are integers, and the product is
    formed in float before the square root.
  - Tau-c and tau-a are not given.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - `N ≥ 2`.
  - Neither record has every value equal.

## Consequences

- The count is direct, `O(N²)`. Knight's `O(N log N)` method is not used.
- **Vectors.**
  - The generator counts the pairs and the ties in integers, then takes the square root and
    the quotient in float.
  - The tolerance is `abs 1e-15, rel 1e-14`.
