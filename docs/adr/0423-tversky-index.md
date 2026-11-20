# ADR 0423: The Tversky index

Status: accepted, 2026-11-19.

## Context

The Tversky index weighs the two kinds of mismatch between a truth record and a decision
record separately: `TP / (TP + α·FN + β·FP)`. At `α = β = 1` it is the Jaccard index
(ADR 0388); at `α = β = ½` it is the Dice coefficient, the F1 score. Other weights trade
missed events against false alarms, as a detector's tuning does.

## Decision

- **The API.**
  - Python: `tversky_index(truth, decision, alpha, beta)` in `measurements`, giving a float.
  - C#: `Measurements.TverskyIndex(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision,
    double alpha, double beta)`.
- **The value.**
  - `TP` counts the items both mark 1, `FN` those only `truth` marks 1, `FP` those only
    `decision` marks 1.
  - The denominator is evaluated as `(TP + α·FN) + β·FP` in that order, then one division,
    so both languages round alike.
  - From 0 to 1, since every term is non-negative.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - `alpha` and `beta` finite and at least 0.
  - A zero denominator is an error: no 1 in either record, or `TP = 0` with every weighted
    mismatch zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the sets directly and forms the index in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
