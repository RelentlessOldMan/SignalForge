# ADR 0352: Auto mutual information

Status: accepted, 2026-11-18.

## Context

Choosing the delay `τ` for every embedding-based measure (ADR 0325 onward) is a standing
question. Fraser and Swinney (1986) suggested the first minimum of the mutual information
between `x_t` and `x_{t+τ}`. Unlike the autocorrelation, it sees nonlinear dependence. The
simplest estimate, and the usual one, is a histogram.

## Decision

- **The API.**
  - Python: `auto_mutual_information(samples, lags, bins=16)` in `measurements`, giving a
    float64 array with one value per lag.
  - C#: `Measurements.AutoMutualInformation(ReadOnlySpan<double> samples,
    ReadOnlySpan<int> lags, int bins = 16)`, giving `double[]`.
- **The bins.**
  - With `lo` and `hi` the smallest and largest sample and `B = bins`, sample `x` goes in
    bin `min(B − 1, floor((x − lo)·B/(hi − lo)))`.
  - The same bins serve both coordinates and every lag.
- **The value.**
  - At lag `τ` the pairs are `(x_t, x_{t+τ})` for `t = 0 … N − τ − 1`, `n = N − τ` of
    them.
  - With `c_ab` the pairs in joint bin `(a, b)`, and `c_a` and `c_b` the counts of the first
    and second coordinates over those same pairs, the value is
    `Σ (c_ab/n)·ln(c_ab·n/(c_a·c_b))`, in nats, over the joint bins with `c_ab > 0`.
  - At lag 0 this is the entropy of the histogram.
- **The rules.**
  - `samples` real, one-dimensional and finite, and not all equal.
  - `lags` a non-empty list of integers, each from 0 to `N − 1`, in any order.
  - `bins` an integer from 2 to 4096.

## Consequences

- **Vectors.**
  - The samples are dyadic. The generator takes each bin exactly in rationals. It asserts
    that no `(x − lo)·B/(hi − lo)` below `B` is within `1e-9` of an integer unless it is
    exactly one. An exact one is exact in float too, since `x − lo`, its product with `B`,
    and `hi − lo` are all exact.
  - The counts are exact, and the sum is taken in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
