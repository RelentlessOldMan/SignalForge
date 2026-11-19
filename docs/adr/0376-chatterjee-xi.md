# ADR 0376: Chatterjee's xi

Status: accepted, 2026-11-19.

## Context

Chatterjee (2021) gave a rank coefficient that tends to 0 when `y` is independent of `x` and
to 1 when `y` is a measurable function of `x`, of any shape. Unlike every other correlation in
`measurements` it is not symmetric: it measures how well `x` predicts `y`.

## Decision

- **The API.**
  - Python: `chatterjee_xi(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.ChatterjeeXi(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The order.**
  - The pairs are sorted by `x`. Chatterjee breaks ties in `x` at random; here they keep their
    order in the record (a stable sort), so the value is deterministic and the same in both
    languages.
- **The value.**
  - In that order, `r_i` counts the samples with `y_j ≤ y_(i)` and `l_i` those with
    `y_j ≥ y_(i)`, over the whole record.
  - `ξ = 1 − N Σ_{i=1}^{N−1} |r_{i+1} − r_i| / (2 Σ_i l_i (N − l_i))`.
  - Without ties in `y` this is `1 − 3 Σ |r_{i+1} − r_i| / (N² − 1)`; its largest value is
    `1 − 3/(N + 1)`, and it can be a little below 0.
  - Both sums are integers, formed exactly; the value is `1 − (N S)/(2 T)` in float.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - `N ≥ 2`, and `y` not constant (the denominator is then 0).

## Consequences

- The cost is two sorts and `N` binary searches.
- **Vectors.**
  - The generator sorts and counts by brute force in integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
