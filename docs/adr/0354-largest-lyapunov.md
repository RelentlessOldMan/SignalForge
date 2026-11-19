# ADR 0354: Largest Lyapunov exponent

Status: accepted, 2026-11-18.

## Context

The largest Lyapunov exponent measures how fast nearby trajectories separate. It is positive
for chaos. Rosenstein, Collins and De Luca (1993) estimate it from one record. They pair
each embedded point with its nearest neighbour that is not close in time, follow both pairs
forward, and average the log of their distance at each step. The exponent is the slope of
that average over the steps where it is straight, so the whole curve is returned as well,
as with the correlation sum (ADR 0349).

## Decision

- **The API.**
  - Python: `largest_lyapunov(samples, m, steps, delay=1, theiler=0)` in `measurements`,
    giving a frozen dataclass `LargestLyapunov(divergence, exponent)`.
  - C#: `Measurements.LargestLyapunov(ReadOnlySpan<double> samples, int m, int steps,
    int delay = 1, int theiler = 0)`, giving the record
    `LargestLyapunov(double[] Divergence, double Exponent)`.
- **The pairs.**
  - The vectors are embedded as for the correlation sum, `W = N − (m − 1)τ` of them.
  - Only the first `P = W − K` take part, where `K = steps`, so that each can move on `K`
    steps.
  - Each `j < P` is paired with the `j'` among them, with `|j − j'| > w`, that is nearest
    in the **Chebyshev** distance. Ties go to the lowest `j'`.
  - Rosenstein used the Euclidean distance. The Chebyshev distance is exact for exact
    samples, so neighbour ties are the same in both languages.
- **The value.**
  - `d_j(k)` is the Chebyshev distance between `v_{j+k}` and `v_{j'+k}`.
  - `divergence[k]`, for `k = 0 … K`, is the mean of `ln d_j(k)` over the `j` with
    `d_j(k) > 0`.
  - `exponent` is the least-squares slope of `divergence` against `k`, per sample.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `m`, `delay` and `steps` integers of at least 1, and `theiler` of at least 0.
  - `P ≥ 2w + 2`, so that every point has a candidate neighbour.
  - At every `k`, at least one `d_j(k)` must be above 0.

## Consequences

- **Vectors.**
  - The samples are dyadic. The generator finds the neighbours and the distances exactly
    in rationals. The logarithms, means and slope are taken in float.
  - The cases include exact distance ties.
  - The tolerance is `abs 1e-12, rel 1e-12`.
