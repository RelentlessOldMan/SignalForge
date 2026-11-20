# ADR 0431: Yule's Y

Status: accepted, 2026-11-19.

## Context

Yule's Y, the coefficient of colligation, is the companion of Yule's Q (ADR 0430) on the
same 2×2 table: `(√x − √y) / (√x + √y)` with `x = TP·TN` and `y = FN·FP`. With the odds
ratio `OR = x / y` it is `(√OR − 1) / (√OR + 1)`, and `Q = 2Y / (1 + Y²)`. It lies nearer 0
than Q for the same table, so it separates strong associations that Q crowds against ±1.

## Decision

- **The API.**
  - Python: `yule_y(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.YuleY(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
- **The value.**
  - `x` and `y` as exact integers, each converted to a double once (exact below `2⁵³`, as
    in ADR 0430), then `sx = √x` and `sy = √y` correctly rounded, then
    `(sx − sy) / (sx + sy)`: the same operations in the same order in both languages.
  - From −1 to 1. Symmetric in the two records.
- **The rules.**
  - As for Yule's Q: records as for the Jaccard index; `x + y = 0` is an error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the roots in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`: a few roundings, and the difference cancels
    when `x` is near `y`.
