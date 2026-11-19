# ADR 0363: Bartels rank test

Status: accepted, 2026-11-18.

## Context

Bartels (1982) made the von Neumann ratio (ADR 0362) distribution-free by applying it to the
ranks of the samples. The test of randomness that results is more powerful than the runs test
against many alternatives.

## Decision

- **The API.**
  - Python: `bartels_rank_test(samples)` in `measurements`, giving a frozen dataclass
    `BartelsRankTest(ratio, z)`.
  - C#: `Measurements.BartelsRankTest(ReadOnlySpan<double> samples)`, giving the record
    `BartelsRankTest(double Ratio, double Z)`.
- **The value.**
  - `R_t` is the rank of `x_t`, from 1 to `N`. Tied samples all get the mean of the ranks
    they span.
  - `ratio = Σ_{t<N−1} (R_{t+1} − R_t)² / Σ_t (R_t − R̄)²`, with `R̄ = (N + 1)/2`.
  - With ties the denominator is the actual sum, not `N(N² − 1)/12`.
  - `z = (ratio − 2)/σ`, with `σ² = 4(N − 2)(5N² − 2N − 9)/(5N(N + 1)(N − 1)²)`. This is
    Bartels's large-sample variance. SignalForge does not adjust it for ties.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `N ≥ 3`, and not every sample equal.

## Consequences

- **Vectors.**
  - The ranks and the ratio are exact in rationals, and so is `σ²`.
  - The square root and the quotient are taken in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
