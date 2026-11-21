# ADR 0522: The Wolfson polarization index

Status: accepted, 2026-11-20.

## Context

Wolfson (1994) measures how far a record has spread away from its middle: twice the gap
between the line of equality and the Lorenz curve at the median holder, less the Gini
coefficient, scaled by the mean over the median. Its parts each have choices of their own:
the median of an even count, where the Lorenz curve is read between points, and the Gini
coefficient's divisor.

## Decision

- **The API.**
  - Python: `wolfson_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.WolfsonIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `W = 2·(μ/m)·(1 − 2·L(1/2) − G)`, with:
    - `μ` the mean and `m` the median, the middle value or `(a + b)/2` of the two middle
      values;
    - `L(1/2)` the Lorenz curve (ADR 0517) joined by straight lines: `n = 2j + r` gives
      `L(1/2) = (S_j + (r/2)·x₍ⱼ₎)/Sₙ`, `x₍ₖ₎` sorted from 0 and `Sₖ` their running sums;
    - `G` the Gini coefficient of ADR 0510, `Σₖ (2k − n + 1)·x₍ₖ₎/(n·Sₙ)`.
  - Formed as `2·(Sₙ − 2·(S_j + (r/2)·x₍ⱼ₎) − g/n)/(n·m)`, `g = Σₖ (2k − n + 1)·x₍ₖ₎`
    summed from `k = 0` upward, the same steps in both languages.
  - At least 0, since the curve is convex and lies above its tangent at `1/2`; 0 when every
    value is equal. Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0.
  - The median must be above 0, so an all-0 record fails too.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator forms each part from its own definition in rationals: the median from
    the middle values, `L(1/2)` by reading the Lorenz points between `k/n`, and `G` from
    the pairwise sum `Σᵢⱼ |xᵢ − xⱼ|/(2n·Sₙ)`.
  - The tolerance is `abs 1e-14, rel 1e-13`.
