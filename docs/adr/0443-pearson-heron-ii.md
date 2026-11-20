# ADR 0443: The Pearson-Heron II coefficient

Status: accepted, 2026-11-19.

## Context

The Pearson-Heron II coefficient of two binary records is
`cos(π·√y / (√x + √y))`, with `x = TP·TN` and `y = FN·FP` as for Yule's Q (ADR 0430): an
approximation of the tetrachoric correlation of the 2x2 table. Since
`√y / (√x + √y) = (1 − Y) / 2` with `Y` Yule's Y (ADR 0431), it equals `sin(π·Y / 2)`.
1 when `y = 0`, −1 when `x = 0`, 0 when `x = y`.

## Decision

- **The API.**
  - Python: `pearson_heron_ii(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.PearsonHeronII(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `x` and `y` exact integers, each converted to a double once and rooted once
    (`sx`, `sy`), then `cos(π·sy / (sx + sy))`: the product `π·sy` first, then the
    division, then the cosine, in that order in both languages.
  - The two languages' cosines need not round alike, so the results may differ in the last
    bit or two.
  - From −1 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `x + y = 0` is an error, as for Yule's Q.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, takes the roots in 40-digit decimals and
    sums the cosine's Taylor series there, with π from Machin's formula.
  - The tolerance is `abs 1e-15, rel 1e-14`: the cosine is near 0 when `x` is near `y`.
