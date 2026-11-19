# ADR 0360: Turning point test

Status: accepted, 2026-11-18.

## Context

The turning point test is a simple, distribution-free test of whether a record is i.i.d. It
counts the samples that are strictly above or strictly below both neighbours. For `N`
i.i.d. continuous samples, the count has mean `2(N − 2)/3` and variance `(16N − 29)/90`
(Kendall and Stuart). Too few turning points means a trend or smooth correlation. Too many
means the record alternates.

## Decision

- **The API.**
  - Python: `turning_points(samples)` in `measurements`, giving a frozen dataclass
    `TurningPoints(count, z)`.
  - C#: `Measurements.TurningPoints(ReadOnlySpan<double> samples)`, giving the record
    `TurningPoints(int Count, double Z)`.
- **The value.**
  - `count` is the number of `i` from 1 to `N − 2` with either `x_{i−1} < x_i > x_{i+1}` or
    `x_{i−1} > x_i < x_{i+1}`.
  - A tie with either neighbour is not a turning point. The test assumes continuous samples,
    so ties should be rare. SignalForge does not adjust for them.
  - `z = (count − 2(N − 2)/3)/√((16N − 29)/90)`.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `N ≥ 3`.

## Consequences

- **Vectors.**
  - The comparisons are exact for any floats, so the count is exact.
  - The generator takes `count − mean` and the variance in rationals, then the square root
    and the quotient in float.
  - The tolerance on `z` is `abs 1e-14, rel 1e-13`.
