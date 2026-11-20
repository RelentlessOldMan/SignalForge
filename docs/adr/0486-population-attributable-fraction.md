# ADR 0486: The population attributable fraction

Status: accepted, 2026-11-20.

## Context

The population attributable fraction treats the decision as an exposure and the truth as an
outcome: the share of all the truth 1s that would go if the exposed group had the risk of
the unexposed. With `P(A) = |A| / n` and the unexposed risk `FN / (FN + TN)` it is
`(P(A) − FN / (FN + TN)) / P(A)`, which is `1 − n·FN / (|A|·(FN + TN))`. It equals the
attributable fraction among the exposed (ADR 0485) times `TP / |A|`. 0 when the records are
independent, 1 when no unexposed item is a 1.

## Decision

- **The API.**
  - Python: `population_attributable_fraction(truth, decision)` in `measurements`, giving a
    float.
  - C#: `Measurements.PopulationAttributableFraction(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - With `u = |A|·(FN + TN)`, the exact integers `u − n·FN` and `u` are each converted to a
    double once; then one division.
  - At most 1, with no lower bound. Not symmetric: `decision` gives the exposure groups.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Truth with no 1 is an error, and so is a decision with no 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
