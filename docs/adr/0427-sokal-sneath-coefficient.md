# ADR 0427: The Sokal-Sneath coefficient

Status: accepted, 2026-11-19.

## Context

The Sokal-Sneath coefficient of two binary records is `TP / (TP + 2·(FN + FP))`: the
Jaccard index (ADR 0388) with each mismatch counted twice, the presence-only counterpart of
the Rogers-Tanimoto coefficient (ADR 0425). It is the Tversky index (ADR 0423) at
`α = β = 2`, given here by name because it is the usual one asked for.

## Decision

- **The API.**
  - Python: `sokal_sneath_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.SokalSneathCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP / (TP + 2·(FN + FP))` from integer counts, the denominator an integer, then one
    division.
  - From 0 to 1; with `J` the Jaccard index it is `J / (2 − J)`. Symmetric.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Neither record holding a 1 is an error: the denominator is zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly; the value is a ratio of integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
