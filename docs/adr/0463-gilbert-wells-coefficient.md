# ADR 0463: The Gilbert-Wells coefficient

Status: accepted, 2026-11-20.

## Context

The Gilbert-Wells coefficient of two binary records is `ln(n·TP / (|A|·|B|))`: the log of
how many times more often the two records share a 1 than independent records with the same
margins would. 0 at independence, positive above it, negative below; undefined when no 1 is
shared.

## Decision

- **The API.**
  - Python: `gilbert_wells_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.GilbertWellsCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `n·TP` and `|A|·|B|` are each converted to a double once, divided
    once, and the platform's natural `log` taken of the quotient. `log` is not correctly
    rounded, so the two languages may differ in the last bit or two.
  - At most `ln n`. Symmetric in the two records; unchanged when every item is repeated
    the same number of times.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `TP = 0` is an error: the log of 0. It covers a record with no 1.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the logarithm of the exact quotient
    correctly rounded in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
