# ADR 0406: The Hodges–Lehmann shift estimate

Status: accepted, 2026-11-19.

## Context

Cliff's delta (ADR 0400) and the Vargha–Delaney A (ADR 0401) say how often one sample is
larger, without saying by how much. The Hodges–Lehmann estimate (1963) of the shift between
two samples is the median of every difference between a value of one and a value of the
other. It is in the units of the data and, unlike the difference of means, robust to a few
wild values.

## Decision

- **The API.**
  - Python: `hodges_lehmann(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.HodgesLehmann(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - Positive when `x` tends to be larger.
- **The value.**
  - All `m = n_x·n_y` differences `xᵢ − yⱼ` are formed in `double` and sorted. With `m` odd
    the middle one is the estimate; with `m` even it is `(a + b)/2` of the two middle ones,
    one addition and one division.
  - Swapping the samples negates it. Adding a constant to `x` adds it to the estimate.
- **The rules.**
  - Each sample one-dimensional, real and finite, at least 1.

## Consequences

- The cost is `n_x·n_y` differences and their sort, so memory grows as the product; a
  selection algorithm that avoids it is not needed yet.
- **Vectors.**
  - The generator takes the differences exactly in rationals and the median from them.
  - The tolerance is `abs 1e-15, rel 1e-14`: each difference rounds once, which keeps the order.
