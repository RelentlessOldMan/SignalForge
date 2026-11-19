# ADR 0419: The Minkowski distance

Status: accepted, 2026-11-19.

## Context

The Minkowski distance of order `p` is the `Lᵖ` norm of the difference of two vectors:
order 1 is the city-block distance, order 2 the Euclidean distance. A direct sum of powers
overflows or underflows long before the distance itself does, so it is scaled by the largest
difference, as a careful `hypot` is.

## Decision

- **The API.**
  - Python: `minkowski_distance(x, y, order)` in `measurements`, giving a float.
  - C#: `Measurements.MinkowskiDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y,
    double order)`.
  - The order is named `order`, not `p`, which the distribution measures use for a
    distribution.
- **The value.**
  - `d(x, y) = (Σᵢ |xᵢ − yᵢ|^p)^(1/p)`.
  - Computed as `m·(Σᵢ pow(|xᵢ − yᵢ|/m, p))^(1/p)` with `m = max |xᵢ − yᵢ|`: one pass for the
    differences and `m`, one for the terms, summed in order, then `m·pow(sum, 1/p)`. `m = 0`
    gives `0`.
  - Symmetric; a metric for `p ≥ 1`.
- **The rules.**
  - `order` is finite and at least 1 (below 1 the triangle inequality fails).
  - `x` and `y` are real and finite, of equal length at least 1.
  - A difference `xᵢ − yᵢ` beyond the largest double is an error.

## Consequences

- The cost is two passes and one power per index.
- **Vectors.**
  - The generator forms the differences exactly in rationals and the powers in 40-digit
    decimal, with no scaling.
  - The tolerance is `abs 1e-15, rel 1e-13`: each power may differ in the last place between
    the two languages' maths libraries.
