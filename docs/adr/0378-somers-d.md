# ADR 0378: Somers' D

Status: accepted, 2026-11-19.

## Context

Somers (1962) gave an asymmetric form of Kendall's tau (ADR 0370) for predicting one ordered
record from another: the pairs tied in the predictor say nothing about the prediction, so
they leave the denominator, while pairs tied only in the response count against it.

## Decision

- **The API.**
  - Python: `somers_d(x, y)` in `measurements`, giving a float: `d_yx`, `y` predicted from
    `x`. Swapping the arguments gives `d_xy`.
  - C#: `Measurements.SomersD(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - Over all pairs `i < j`, `C` and `D` count the concordant and discordant pairs by
    comparison, as in ADR 0377; `T_x` counts the pairs tied in `x`, whatever `y` does.
  - `d_yx = (C − D)/(N(N − 1)/2 − T_x)`, from −1 to 1.
  - Without ties it is Kendall's tau; in general `d_yx d_xy = τ_b²`.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - At least one pair untied in `x` (so `N ≥ 2` and `x` not constant).

## Consequences

- The direct count is `O(N²)`.
- **Vectors.**
  - The generator counts the pairs by brute force; the value is a ratio of two counts.
  - The tolerance is `abs 1e-15, rel 1e-15`.
