# ADR 0450: Eyraud's coefficient

Status: accepted, 2026-11-19.

## Context

Eyraud's coefficient of two binary records is
`n²·(n·TP − |A|·|B|) / (|A|·|B|·(n − |A|)·(n − |B|))`, with `|A|` and `|B|` the counts of 1.
In shares it is the covariance `TP/n − pA·pB` over the product of the four margins
`pA·pB·(1 − pA)·(1 − pB)`. 0 for independence, positive when the records go together,
negative when they go against each other; it has no fixed ends (identical records with `k`
ones of `n` give `n²/(k·(n − k))`).

## Decision

- **The API.**
  - Python: `eyraud_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.EyraudCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `c = n·TP − |A|·|B|`, `n²`, `u = |A|·|B|` and
    `v = (n − |A|)·(n − |B|)` are each converted to a double once, then
    `c · n² / (u · v)` in that order, the same in both languages.
  - Symmetric in the two records; flipping one record changes its sign.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant record (all 0 or all 1) is an error: then `u · v = 0`.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from the
    shares, as the covariance over the four margins.
  - The tolerance is `abs 1e-15, rel 1e-14`.
