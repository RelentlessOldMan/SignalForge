# ADR 0540: The McIntosh evenness

Status: accepted, 2026-11-21.

## Context

The McIntosh dominance (ADR 0539) depends on the scale of the values. Scaling its
numerator `N − U` by its largest value for the given total and length, `N − N/√n`
(reached when every value is equal), gives an evenness that does not.

## Decision

- **The API.**
  - Python: `mcintosh_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.McIntoshEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = (N − U)/(N − N/√n)`, `N = Σᵢ xᵢ` and `Σᵢ xᵢ²` added in record order, `U` its
    square root, `n` the record length with zero values counted.
  - From 0 (one value holds the total) to 1 (every value equal), as `N/√n ≤ U ≤ N`.
    Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 2 values, every value at least 0,
    not all 0.

## Consequences

- One pass for the total, one for the squares; no sort.
- **Vectors.**
  - The generator forms the sums exactly and the square roots in 50-digit `decimal`.
  - The tolerance is `abs 1e-14, rel 1e-13`: `N − U` loses digits when one value is close
    to the total.
