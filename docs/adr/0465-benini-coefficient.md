# ADR 0465: The Benini coefficient

Status: accepted, 2026-11-20.

## Context

The Benini coefficient of two binary records is
`(n·TP − |A|·|B|) / (n·min(|A|, |B|) − |A|·|B|)`: the excess of the shared 1s over what
independent records with the same margins would share, as a share of the most excess the
margins allow. 1 when the 1s of one record all lie among the 1s of the other, 0 at
independence, negative below it, with no fixed lower end.

## Decision

- **The API.**
  - Python: `benini_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.BeniniCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Numerator and denominator exact integers, each converted to a double once, then one
    division.
  - At most 1. Symmetric in the two records; unchanged when every item is repeated the
    same number of times.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A denominator of 0 is an error. It equals `min(|A|, |B|)·(n − max(|A|, |B|))`, so it
    is 0 exactly when a record has no 1 or a record is all 1.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
