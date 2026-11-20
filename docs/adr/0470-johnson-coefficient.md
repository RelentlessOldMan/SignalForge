# ADR 0470: The Johnson coefficient

Status: accepted, 2026-11-20.

## Context

The Johnson coefficient of two binary records is `TP/|A| + TP/|B|`: the share of the first
record's 1s that the second shares, plus the converse. Twice the Kulczynski coefficient
(ADR 0428). 2 when the records are equal, 0 when they share
no 1.

## Decision

- **The API.**
  - Python: `johnson_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.JohnsonCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP/|A|` and `TP/|B|`, each a quotient of exact integers converted to doubles once,
    added in that order.
  - From 0 to 2. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A record with no 1 is an error: its share is then 0/0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
