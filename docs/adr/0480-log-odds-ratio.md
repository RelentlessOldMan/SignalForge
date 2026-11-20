# ADR 0480: The log odds ratio

Status: accepted, 2026-11-20.

## Context

The log odds ratio of two binary records is `ln(TP·TN / (FN·FP))`, the natural log of the
diagnostic odds ratio. 0 when the records are independent; it changes sign when one record
is complemented.

## Decision

- **The API.**
  - Python: `log_odds_ratio(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.LogOddsRatio(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP·TN` and `FN·FP` are each converted to a double once; then one
    division and the platform's natural `log`.
  - Any real number. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A zero cell is an error: the ratio is then 0 or infinite, or undefined.
  - No correction such as adding 1/2 to each cell.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, forms the ratio in rationals and takes its
    natural log in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
