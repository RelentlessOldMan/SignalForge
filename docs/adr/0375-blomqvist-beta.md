# ADR 0375: Blomqvist's beta

Status: accepted, 2026-11-19.

## Context

Blomqvist (1950) proposed the medial correlation: split each record at its median and count
how often the two records fall on the same side. It needs only the two medians and a count,
so it is very robust, and for a bivariate normal pair with correlation `ρ` it estimates
`(2/π) arcsin ρ`, the same as Kendall's tau (ADR 0370).

## Decision

- **The API.**
  - Python: `blomqvist_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.BlomqvistBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The medians.**
  - The middle value for odd `N`; for even `N`, `(a + b)/2` of the two middle values, in that
    order of operations, so both languages compare against the same float.
- **The value.**
  - A sample with `x_i` equal to the median of `x` or `y_i` equal to the median of `y` is
    dropped.
  - Of the rest, `n₊` lie on the same side of both medians and `n₋` on opposite sides.
  - `β = (n₊ − n₋)/(n₊ + n₋)`, from −1 to 1.
  - Some texts give the samples on a median half a count each way; dropping them is the
    convention here, and it keeps the value at ±1 for a monotone pair.
- **The rules.**
  - `x` and `y` real, one-dimensional, finite and the same length.
  - At least one sample off both medians (so `N ≥ 2`).

## Consequences

- The cost is two sorts.
- **Vectors.**
  - The generator finds the medians and counts exactly in rationals, on eighths so the float
    median is exact too.
  - The value is a ratio of two counts; the tolerance is `abs 1e-15, rel 1e-15`.
