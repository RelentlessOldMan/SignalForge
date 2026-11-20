# ADR 0459: The fourth Sokal-Sneath coefficient

Status: accepted, 2026-11-20.

## Context

The fourth of Sokal and Sneath's coefficients for two binary records is the mean of the
four conditional probabilities of agreement: `TP/|A|` and `TP/|B|` for a 1 in either
record, `TN/(n − |A|)` and `TN/(n − |B|)` for a 0. 1 when the records agree everywhere, 0
when they disagree everywhere, 1/2 when they are independent. The first coefficient of the
series is already `sokal_sneath_coefficient` (ADR 0427), so this one carries its number.

## Decision

- **The API.**
  - Python: `sokal_sneath_iv(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.SokalSneathIV(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The four quotients, each of two exact integers converted to doubles once, summed in the
    order above, then divided by 4.
  - From 0 to 1. Symmetric in the two records; unchanged when both records are flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant record is an error: one of the four denominators is then 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the four quotients and their mean in
    rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`: four roundings are summed.
