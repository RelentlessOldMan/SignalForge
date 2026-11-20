# ADR 0421: The Hamming distance

Status: accepted, 2026-11-19.

## Context

The Hamming distance counts the positions at which two sequences differ: the number of
symbol errors between a sent and a received block, or the number of samples a processed
signal changed. `bit_errors` works on bits; this takes any real
values, such as symbol indices or quantized levels.

## Decision

- **The API.**
  - Python: `hamming_distance(x, y)` in `measurements`, giving an int.
  - C#: `Measurements.HammingDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`,
    giving an `int`.
- **The value.**
  - The number of indices `i` with `xᵢ ≠ yᵢ`, compared as doubles: `0.0` and `−0.0` are
    equal.
  - From 0 to the length. Symmetric, a metric.
- **The rules.**
  - `x` and `y` are real and finite, of equal length at least 1 (a NaN would differ from
    itself).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the differences directly; the results are exact integers.
