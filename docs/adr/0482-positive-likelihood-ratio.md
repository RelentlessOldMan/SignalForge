# ADR 0482: The positive likelihood ratio

Status: accepted, 2026-11-20.

## Context

The positive likelihood ratio of a binary decision against a binary truth is the true
positive rate over the false positive rate: `(TP / |A|) / (FP / (n − |A|))`, which is
`TP·(FP + TN) / (|A|·FP)`. 1 when the decision is independent of the truth; larger is a
better test.

## Decision

- **The API.**
  - Python: `positive_likelihood_ratio(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.PositiveLikelihoodRatio(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP·(FP + TN)` and `|A|·FP` are each converted to a double once; then
    one division.
  - At least 0. Not symmetric: `truth` gives the rows.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Truth with no 1 is an error, and so is `FP = 0` (this covers truth with no 0).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
