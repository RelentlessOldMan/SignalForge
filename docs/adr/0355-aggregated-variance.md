# ADR 0355: Aggregated variance

Status: accepted, 2026-11-18.

## Context

The aggregated-variance method (Beran, 1994; Taqqu, Teverovsky and Willinger, 1995) is the
simplest Hurst estimator, next to rescaled range (ADR 0340) and detrended fluctuation
(ADR 0332). The means of blocks of `s` samples have a variance that falls as `s^{2H − 2}`
for a long-memory stationary process, and as `s^{−1}` for white noise, where `H = 1/2`.

## Decision

- **The API.**
  - Python: `aggregated_variance(samples, sizes)` in `measurements`, giving a frozen
    dataclass `AggregatedVariance(sizes, values, hurst)`.
  - C#: `Measurements.AggregatedVariance(ReadOnlySpan<double> samples,
    ReadOnlySpan<int> sizes)`, giving the record
    `AggregatedVariance(int[] Sizes, double[] Values, double Hurst)`.
- **The value.**
  - At block size `s`, the first `B·s` samples, with `B = floor(N/s)`, are cut into `B`
    blocks, and any leftover samples are dropped.
  - `values` is the **population** variance (over `B`) of the `B` block means.
  - `hurst` is `1 + β/2`, where `β` is the least-squares slope of `ln values` against
    `ln s`.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `sizes` holds at least two integers, strictly increasing, each at least 1 and at most
    `N/2`, so that there are at least two blocks.
  - Every value must be above 0, or the logarithm is undefined; that is an error.

## Consequences

- **Vectors.**
  - The block means and their variances are exact in rationals.
  - The slope is taken in float.
  - The tolerance is `abs 1e-12, rel 1e-12`.
