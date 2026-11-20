# ADR 0490: The extremal dependence index

Status: accepted, 2026-11-20.

## Context

The extremal dependence index of a binary forecast against a binary truth is
`(ln F − ln H) / (ln F + ln H)`, with the hit rate `H = TP / |A|` and the false alarm rate
`F = FP / (n − |A|)`. Unlike the extreme dependency score (ADR 0489) it uses both rates, so
it does not depend on the base rate. Both logarithms are at most 0, so the value is from
−1 to 1: 1 when `H = 1`, −1 when `F = 1`, 0 when `H = F`.

## Decision

- **The API.**
  - Python: `extremal_dependence_index(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.ExtremalDependenceIndex(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `ln F` and `ln H` are each the natural logarithm of one division of two counts, each
    converted to a double once; then one subtraction, one addition and one division.
  - From −1 to 1. Not symmetric: `truth` gives the rows.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant truth is an error, and so are `TP = 0` and `FP = 0` (the logarithm of 0),
    and `H = F = 1` (a decision of all 1, a zero denominator).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the logarithms in 40-digit decimals.
  - The tolerance is `abs 1e-13, rel 1e-13`.
