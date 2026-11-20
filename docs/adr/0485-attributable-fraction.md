# ADR 0485: The attributable fraction

Status: accepted, 2026-11-20.

## Context

The attributable fraction among the exposed is `(RR − 1) / RR`, with RR the relative risk
of ADR 0484 (the decision as the exposure, the truth as the outcome): the share of the
exposed group's 1s that the exposure accounts for. Written in the cells it is
`(TP·(FN + TN) − FN·(TP + FP)) / (TP·(FN + TN))`. 0 when the records are independent, 1
when no unexposed item is a 1, and negative when the exposure protects.

## Decision

- **The API.**
  - Python: `attributable_fraction(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.AttributableFraction(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP·(FN + TN) − FN·(TP + FP)` and `TP·(FN + TN)` are each converted
    to a double once; then one division. Forming `1 − 1/RR` in doubles is not used: it
    rounds twice.
  - At most 1, with no lower bound. Not symmetric: `decision` gives the exposure groups.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `TP = 0` is an error (RR is then 0), and so is a decision with no 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
