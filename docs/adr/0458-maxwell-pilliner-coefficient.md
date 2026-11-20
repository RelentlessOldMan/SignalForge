# ADR 0458: The Maxwell-Pilliner coefficient

Status: accepted, 2026-11-20.

## Context

The Maxwell-Pilliner coefficient of two binary records is
`2·(TP·TN − FN·FP) / ((TP + FN)·(FP + TN) + (TP + FP)·(FN + TN))`: the cross-product
difference over the sum of the two records' own variances (times `n²`), not their
geometric mean as in the phi coefficient. 1 when the records agree everywhere, −1 when they
disagree everywhere, 0 when they are independent.

## Decision

- **The API.**
  - Python: `maxwell_pilliner_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.MaxwellPillinerCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - With `|A| = TP + FN`, `|B| = TP + FP`, the denominator as
    `|A|·(n − |A|) + |B|·(n − |B|)`: numerator and denominator exact integers, each
    converted to a double once, then one division.
  - From −1 to 1, at most the phi coefficient in size. Symmetric in the two records;
    unchanged when both records are flipped; changes sign when one is.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A zero denominator is an error: that is both records constant. One constant record
    alone is not: the value is then 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from the four
    cells as written.
  - The tolerance is `abs 1e-15, rel 1e-15`.
