# ADR 0444: Digby's H

Status: accepted, 2026-11-19.

## Context

Digby's H of two binary records is `(x^(3/4) − y^(3/4)) / (x^(3/4) + y^(3/4))`, with
`x = TP·TN` and `y = FN·FP` as for Yule's Q (ADR 0430). Yule's Q is the same form with power
1 and Yule's Y (ADR 0431) with power 1/2; Digby chose 3/4 as a better approximation of the
tetrachoric correlation. H always lies between Y and Q. 1 when `y = 0`, −1 when `x = 0`,
0 when `x = y`.

## Decision

- **The API.**
  - Python: `digby_h(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.DigbyH(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
- **The value.**
  - `x` and `y` exact integers, each converted to a double once. The power 3/4 is taken as
    `√v · √√v` from correctly rounded square roots, not with a general power function, so
    that both languages get the same bits: `sx = √x`, `px = sx·√sx`, and likewise `py`.
    Then `(px − py) / (px + py)`.
  - From −1 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `x + y = 0` is an error, as for Yule's Q.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the roots in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
