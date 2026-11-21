# ADR 0498: The Wald z of the log odds ratio

Status: accepted, 2026-11-20.

## Context

The Wald statistic for independence in a 2x2 table divides the log odds ratio
(ADR 0480) by its standard error (ADR 0493): `z = ln(x/y) / SE` with `x = TP·TN`,
`y = FN·FP` and `SE = sqrt(1/TP + 1/FN + 1/FP + 1/TN)`. Since `SE² = N / (xy)`, with
`N = FN·FP·TN + TP·FP·TN + TP·FN·TN + TP·FN·FP`, it is `ln(x/y)·sqrt(xy / N)`.

## Decision

- **The API.**
  - Python: `log_odds_ratio_wald_z(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.LogOddsRatioWaldZ(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `ln(x/y)·sqrt(xy / N)`: the exact integers `x`, `y`, `xy` and `N` are each converted to
    a double once; one division and the logarithm, one division and the square root, then
    the product.
  - Any real value; 0 exactly when `x = y`. Symmetric in the two records; it changes sign
    when the decision is complemented.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Any cell equal to 0 is an error, as for the standard error of the log odds ratio.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the logarithm and the square root in
    40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
