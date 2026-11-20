# ADR 0483: The negative likelihood ratio

Status: accepted, 2026-11-20.

## Context

The negative likelihood ratio of a binary decision against a binary truth is the false
negative rate over the true negative rate: `(FN / |A|) / (TN / (n − |A|))`, which is
`FN·(FP + TN) / (|A|·TN)`. 1 when the decision is independent of the truth; smaller is a
better test. It is the companion of the positive likelihood ratio (ADR 0482).

## Decision

- **The API.**
  - Python: `negative_likelihood_ratio(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.NegativeLikelihoodRatio(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `FN·(FP + TN)` and `|A|·TN` are each converted to a double once; then
    one division.
  - At least 0. Not symmetric: `truth` gives the rows.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Truth with no 1 is an error, and so is `TN = 0` (this covers truth with no 0).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
