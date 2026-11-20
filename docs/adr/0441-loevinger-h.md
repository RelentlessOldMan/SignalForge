# ADR 0441: Loevinger's H

Status: accepted, 2026-11-19.

## Context

Loevinger's H of two binary records is the covariance of the records over the largest
covariance two records with the same counts of 1 could have:
`(TP/n − pA·pB) / (min(pA, pB) − pA·pB)`, with `pA = |A|/n` and `pB = |B|/n`. In counts it
is `(n·TP − |A|·|B|) / (n·min(|A|, |B|) − |A|·|B|)`. It is 1 whenever the 1s of one record
lie inside the other's, 0 for independence, and the phi coefficient (Matthews correlation)
over the largest phi the counts allow. At most 1; it has no fixed lower bound.

## Decision

- **The API.**
  - Python: `loevinger_h(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.LoevingerH(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The numerator and the denominator in counts are exact integers, each converted to a
    double once (exact below `2⁵³`, which holds for any record shorter than `2²⁶` items),
    then one division.
  - At most 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A zero denominator is an error. It is zero exactly when a record is constant: all 0
    (`min(|A|, |B|) = 0`) or all 1 (`max(|A|, |B|) = n`).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from the
    shares `TP/n`, `pA` and `pB`, not from the count form.
  - The tolerance is `abs 1e-15, rel 1e-15`.
