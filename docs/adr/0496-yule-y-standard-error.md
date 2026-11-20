# ADR 0496: The standard error of Yule's Y

Status: accepted, 2026-11-20.

## Context

Yule's Y is `(√x − √y) / (√x + √y)` with `x = TP·TN` and `y = FN·FP`. Its large-sample
(delta-method) standard error is `¼·(1 − Y²)·SE`, where
`SE = sqrt(1/TP + 1/FN + 1/FP + 1/TN)` is the standard error of the log odds ratio
(ADR 0493). Since `1 − Y² = 4·√(xy) / (√x + √y)²` and `xy·SE² = N`, with
`N = FN·FP·TN + TP·FP·TN + TP·FN·TN + TP·FN·FP`, it is `√N / (√x + √y)²`.

## Decision

- **The API.**
  - Python: `yule_y_standard_error(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.YuleYStandardError(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `√N / (√x + √y)²`: the exact integers `N`, `x` and `y` are each converted to a double
    once and their square roots taken; the sum of the two roots is squared; then one
    division.
  - Above 0, at most `¼·SE`. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Any cell equal to 0 is an error, as for the standard error of the log odds ratio.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the square roots in 40-digit
    decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
