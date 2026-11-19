# ADR 0367: Buishand range test

Status: accepted, 2026-11-18.

## Context

Buishand (1982) tests a record for a change in its mean using the partial sums of its
deviations from the mean. A shift makes the partial sums drift away from 0 and then back. It
is used alongside Pettitt's test (ADR 0366) in climate homogeneity work.

## Decision

- **The API.**
  - Python: `buishand_range(samples)` in `measurements`, giving a frozen dataclass
    `BuishandRange(q, r, index)`.
  - C#: `Measurements.BuishandRange(ReadOnlySpan<double> samples)`, giving the record
    `BuishandRange(double Q, double R, int Index)`.
- **The value.**
  - The mean is `x̄ = (Σ x)/N`, in float.
  - The partial sums are `S_k = Σ_{i≤k} (x_i − x̄)` for `k = 0 … N − 1`, summed in order.
  - `σ` is the population standard deviation, `√(Σ (x_i − x̄)²/N)`.
  - `q = max_k |S_k|/σ`.
  - `r = (max(0, max_k S_k) − min(0, min_k S_k))/σ`. Buishand's `S_0 = 0` is included,
    which also stands for `S_{N−1}`, exactly 0 in exact arithmetic.
  - `index` is the smallest `k` with the largest `|S_k|`. It is the last sample before the
    change.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `N ≥ 2`, and not every sample equal.

## Consequences

- **Vectors.**
  - The partial sums depend on the float mean. So the vector samples are dyadic, with an
    exact float mean (asserted), and every partial sum is then exact.
  - The generator takes the partial sums and `σ²` in rationals, then the square root and the
    quotients in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
