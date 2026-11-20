# ADR 0428: The Kulczynski coefficient

Status: accepted, 2026-11-19.

## Context

The Kulczynski coefficient (the second one Kulczynski gave) of two binary records is the
mean of the shares of each record's 1s that the other also marks:
`½·(TP/|A| + TP/|B|)`. Against a truth record these are the recall and the precision, so it
is their arithmetic mean, where the F1 score is their harmonic mean.

## Decision

- **The API.**
  - Python: `kulczynski_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.KulczynskiCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `(TP/|A| + TP/|B|) / 2`, evaluated in that order: two divisions of integer counts, a sum
    and a halving, so both languages round alike.
  - From 0 to 1; at least the F1 score. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Either record with no 1 is an error: its share is undefined.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
