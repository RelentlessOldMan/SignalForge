# ADR 0471: The dispersion coefficient

Status: accepted, 2026-11-20.

## Context

The dispersion coefficient of two binary records is `(TP·TN − FN·FP) / n²`: the population
covariance of the two records as 0/1 values. 0 when they are independent, 1/4 when they
are equal and half 1s, −1/4 when they are opposite and half 1s.

## Decision

- **The API.**
  - Python: `dispersion_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.DispersionCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP·TN − FN·FP` and `n²` are each converted to a double once;
    then one division.
  - From −1/4 to 1/4. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Constant records are allowed; the value is then 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
