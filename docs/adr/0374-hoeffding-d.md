# ADR 0374: Hoeffding's D

Status: accepted, 2026-11-18.

## Context

Hoeffding (1948) built a rank test of independence that, like the distance correlation
(ADR 0372), is consistent against any dependence, monotone or not. It uses only ranks, so it
is unchanged by any increasing map of either record.

## Decision

- **The API.**
  - Python: `hoeffding_d(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.HoeffdingD(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The ranks.**
  - `R_i` and `S_i` are the ranks of `x_i` and `y_i` from 1, ties given the mean rank, as in
    ADR 0363.
  - The bivariate rank is `Q_i = 1 + Σ_{j≠i} φ(x_j, x_i) φ(y_j, y_i)`, with `φ(a, b) = 1`
    for `a < b`, `1/2` for `a = b` and 0 otherwise. This tie rule is the one SAS's
    `PROC CORR` documents.
- **The value.**
  - `D₁ = Σ (Q − 1)(Q − 2)`.
  - `D₂ = Σ (R − 1)(R − 2)(S − 1)(S − 2)`.
  - `D₃ = Σ (R − 2)(S − 2)(Q − 1)`.
  - `D = 30((N − 2)(N − 3)D₁ + D₂ − 2(N − 2)D₃)/(N(N − 1)(N − 2)(N − 3)(N − 4))`.
  - This is the scale on which perfect monotone dependence without ties gives 1, and
    independence gives about 0. The least value is −1/2. Some sources divide by 30.
  - The ranks, `Q` and the three sums are multiples of `1/16`, so for practical `N` they are
    exact in float. The bracket is formed in the order written, then divided by the product
    of the five factors.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - `N ≥ 5`.

## Consequences

- The direct count of `Q` is `O(N²)`.
- **Vectors.**
  - The generator computes the ranks, `Q` and the sums exactly in rationals.
  - The tolerance is `abs 1e-14, rel 1e-13`.
