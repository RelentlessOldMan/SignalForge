# ADR 0488: The frequency bias

Status: accepted, 2026-11-20.

## Context

The frequency bias (bias score) of a binary forecast against a binary truth is the count of
decision 1s over the count of truth 1s, `|B| / |A|`, which is `(TP + FP) / (TP + FN)`. 1
when the decision says 1 as often as the truth does, above 1 when it over-forecasts. It
says nothing about whether the 1s line up.

## Decision

- **The API.**
  - Python: `frequency_bias(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.FrequencyBias(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact counts `|B|` and `|A|` are each converted to a double once; then one division.
  - At least 0. Not symmetric: swapping the records gives the reciprocal.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Truth with no 1 is an error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
