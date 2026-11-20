# ADR 0493: The standard error of the log odds ratio

Status: accepted, 2026-11-20.

## Context

Woolf's large-sample standard error of the log odds ratio (ADR 0480) of two binary records is
`sqrt(1/TP + 1/FN + 1/FP + 1/TN)`. With it, `ln OR ± 1.96·SE` is the usual approximate 95%
interval. It is symmetric in the cells, so swapping the records leaves it unchanged.

## Decision

- **The API.**
  - Python: `log_odds_ratio_standard_error(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.LogOddsRatioStandardError(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The sum of reciprocals is the exact rational `(FN·FP·TN + TP·FP·TN + TP·FN·TN +
    TP·FN·FP) / (TP·FN·FP·TN)`; the two integers are each converted to a double once, then
    one division and the square root.
  - Above 0. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Any cell equal to 0 is an error, as for the log odds ratio.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, sums the reciprocals in rationals and takes the
    square root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
