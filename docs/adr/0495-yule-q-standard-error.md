# ADR 0495: The standard error of Yule's Q

Status: accepted, 2026-11-20.

## Context

Yule's Q is `(x − y) / (x + y)` with `x = TP·TN` and `y = FN·FP`, a function of the odds
ratio. Its large-sample (delta-method) standard error is `½·(1 − Q²)·SE`, where
`SE = sqrt(1/TP + 1/FN + 1/FP + 1/TN)` is the standard error of the log odds ratio
(ADR 0493). Since `1 − Q² = 4xy / (x + y)²` and `xy·SE² = N`, with
`N = FN·FP·TN + TP·FP·TN + TP·FN·TN + TP·FN·FP`, it is `2·sqrt(xy·N) / (x + y)²`.

## Decision

- **The API.**
  - Python: `yule_q_standard_error(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.YuleQStandardError(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `2·sqrt(xy·N) / (x + y)²`: the exact integers `xy` and `N` are each converted to a
    double once and multiplied, then the square root and the doubling; `x + y` is
    converted to a double once and squared; then one division.
  - Above 0, at most `½·SE`. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Any cell equal to 0 is an error, as for the standard error of the log odds ratio.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the square root in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
