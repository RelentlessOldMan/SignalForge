# ADR 0489: The extreme dependency score

Status: accepted, 2026-11-20.

## Context

The extreme dependency score of a binary forecast against a binary truth is
`2·ln(|A| / n) / ln(TP / n) − 1`: a skill score meant for rare events, where scores built
on the table's counts tend to 0 as the base rate falls. Since `TP ≤ |A| ≤ n`, both logarithms
are at most 0 and the ratio lies from 0 to 1, so the score is from −1 to 1: 1 when every
truth 1 is caught (`TP = |A|`), −1 when truth is all 1 and the forecast misses some.

## Decision

- **The API.**
  - Python: `extreme_dependency_score(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.ExtremeDependencyScore(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The counts `|A|`, `TP` and `n` are each converted to a double once; `ln(|A| / n)` and
    `ln(TP / n)` are each the natural logarithm of one division; then
    `2·ln(|A| / n) / ln(TP / n) − 1`.
  - From −1 to 1. Not symmetric: `truth` gives the base rate.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `TP = 0` is an error (the logarithm of 0), and so is `TP = n` (a zero denominator).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the logarithms in 40-digit decimals.
  - The tolerance is `abs 1e-13, rel 1e-13`.
