# ADR 0466: The Doolittle coefficient

Status: accepted, 2026-11-20.

## Context

The Doolittle coefficient of two binary records is
`(n·TP − |A|·|B|)² / (|A|·|B|·(n − |A|)·(n − |B|))`: the square of the phi coefficient,
the share of either record's variance the other explains. 1 when the records agree
everywhere or disagree everywhere, 0 at independence.

## Decision

- **The API.**
  - Python: `doolittle_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.DoolittleCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `x = n·TP − |A|·|B|`, `u = |A|·|B|` and `v = (n − |A|)·(n − |B|)`
    are each converted to a double once; the value is `(x·x) / (u·v)` in doubles. Squaring
    in doubles keeps every integer within 64 bits.
  - From 0 to 1. Symmetric in the two records; unchanged when either record is flipped
    and when every item is repeated the same number of times.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant record is an error: `u·v` is then 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
