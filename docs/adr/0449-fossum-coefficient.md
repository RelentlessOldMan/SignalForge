# ADR 0449: Fossum's coefficient

Status: accepted, 2026-11-19.

## Context

Fossum's coefficient of two binary records is `n·(TP − 1/2)² / (|A|·|B|)`, with `|A|` and
`|B|` the counts of 1 in the two records. It grows with the shared 1s against what the
counts of 1 would give by chance, with a continuity correction of 1/2. It is at least 0
and has no fixed upper end: identical records with `k` ones of `n` give
`n·(k − 1/2)²/k²`.

## Decision

- **The API.**
  - Python: `fossum_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.FossumCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - As `n·(2·TP − 1)² / (4·|A|·|B|)`: numerator and denominator exact integers, each
    converted to a double once (exact below `2⁵³`, which holds for any record shorter than
    `2¹⁷` items), then one division.
  - At least 0. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A record with no 1 is an error: then `|A|·|B| = 0`. A record of all 1 is fine.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms `n·(TP − 1/2)²/(|A|·|B|)` in
    rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
