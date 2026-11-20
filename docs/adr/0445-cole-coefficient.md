# ADR 0445: Cole's coefficient

Status: accepted, 2026-11-19.

## Context

Cole's coefficient scales the cross-product difference `Δ = TP·TN − FN·FP` of two binary
records (which is `n·TP − |A|·|B|`) by the extreme it could reach for the same counts of 1.
With those counts fixed, `TP` runs from `max(0, |A| + |B| − n)` to `min(|A|, |B|)`, so `Δ`
runs from `Δmin = n·max(0, |A| + |B| − n) − |A|·|B|` to `Δmax = n·min(|A|, |B|) − |A|·|B|`.
The coefficient is `Δ / Δmax` when `Δ ≥ 0` (Loevinger's H, ADR 0441) and `Δ / |Δmin|` when
`Δ < 0`, so it runs from −1 to 1 and reaches both ends for any counts. 0 for independence.

## Decision

- **The API.**
  - Python: `cole_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.ColeCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `Δ` and the chosen bound are exact integers, each converted to a double once (exact
    below `2⁵³`, which holds for any record shorter than `2²⁶` items), then one division.
  - From −1 to 1. Symmetric in the two records. Equal to Loevinger's H when `Δ ≥ 0`.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant record (all 0 or all 1) is an error: then `Δmax = Δmin = 0`. For any
    other records both bounds are nonzero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from the
    shares `TP/n`, `pA` and `pB`, not from the count form.
  - The tolerance is `abs 1e-15, rel 1e-15`.
