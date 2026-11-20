# ADR 0457: The Consonni-Todeschini coefficient

Status: accepted, 2026-11-20.

## Context

The Consonni-Todeschini coefficient of two binary records is `ln(1 + TP + TN) / ln(1 + n)`:
the count of matching items on a log scale, so the first few disagreements cost more than
under simple matching. 1 when the records agree everywhere, 0 when they disagree
everywhere.

## Decision

- **The API.**
  - Python: `consonni_todeschini_coefficient(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.ConsonniTodeschiniCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `1 + TP + TN` and `1 + n` are each converted to a double once, then
    the platform's natural `log` of each and one division. `log` is not correctly rounded,
    so the two languages may differ in the last bits.
  - From 0 to 1. Symmetric in the two records; unchanged when both records are flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other error: `ln(1 + n)` is at least `ln 2`.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the two logarithms correctly rounded
    in 40-digit decimals, then their ratio.
  - The tolerance is `abs 1e-15, rel 1e-14`.
