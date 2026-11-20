# ADR 0469: Gower's coefficient

Status: accepted, 2026-11-20.

## Context

Gower's coefficient of two binary records is
`(TP + TN) / sqrt(|A|·|B|·(n − |A|)·(n − |B|))`: the matching items over the geometric
mean of the four margins. 0 when the records disagree everywhere. It has no fixed upper
end: identical records with one 1 among four give 4/3.

## Decision

- **The API.**
  - Python: `gower_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.GowerCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP + TN`, `u = |A|·|B|` and `v = (n − |A|)·(n − |B|)` are each
    converted to a double once; the value is `(TP + TN) / sqrt(u · v)`, as for the fifth
    Sokal-Sneath coefficient (ADR 0460).
  - At least 0. Symmetric in the two records; unchanged when both records are flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant record is an error: `u · v` is then 0.
  - Not the Gower-Legendre coefficient (ADR 0455), which is a weighted simple matching.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, forms the square of the value in rationals
    and takes its correctly rounded square root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
