# ADR 0439: The Gilbert skill score

Status: accepted, 2026-11-19.

## Context

The Gilbert skill score, also called the equitable threat score, rates a binary forecast
(the decision) against what happened (the truth): `(TP − R) / (TP + FN + FP − R)`, with
`R = |A|·|B| / n` the hits a forecast with the same count of 1s would get by chance. It is
the Jaccard index (the threat score, ADR 0388) with the chance hits taken out of both
counts. 1 for a perfect forecast, 0 for one no better than chance, down to `−1/3`.

## Decision

- **The API.**
  - Python: `gilbert_skill_score(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.GilbertSkillScore(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Both parts multiplied by `n` so that they are exact integers:
    `(n·TP − |A|·|B|) / (n·(TP + FN + FP) − |A|·|B|)`. Each converted to a double once
    (exact below `2⁵³`, which holds for any record shorter than `2²⁶` items), then one
    division.
  - From −1/3 to 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A zero denominator is an error. It is zero exactly when the records are equal and
    constant: both all 0, or both all 1.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from `R`
    itself, not from the scaled form.
  - The tolerance is `abs 1e-15, rel 1e-15`.
