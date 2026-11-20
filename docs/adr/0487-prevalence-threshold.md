# ADR 0487: The prevalence threshold

Status: accepted, 2026-11-20.

## Context

The prevalence threshold of a binary test is `(sqrt(TPR·FPR) − FPR) / (TPR − FPR)`, with
the true positive rate `TPR = TP / |A|` and the false positive rate `FPR = FP / (n − |A|)`:
the prevalence below which the test's positive predictive value falls away fastest. The
geometric mean of the two rates lies between them, so the value is from 0 to 1: 0 when
`FPR = 0`, 1 when `TPR = 0`.

## Decision

- **The API.**
  - Python: `prevalence_threshold(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.PrevalenceThreshold(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Multiplying through by `a·b`, with `a = |A|` and `b = n − |A|`, gives
    `(sqrt(TP·FP·a·b) − FP·a) / (TP·b − FP·a)`.
  - The exact integers `TP·FP` and `a·b` are each converted to a double once and
    multiplied; then the square root. `FP·a` and `TP·b − FP·a` are exact integers, each
    converted to a double once; then one subtraction and one division.
  - From 0 to 1. Not symmetric: `truth` gives the rows.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant truth is an error, and so is `TPR = FPR` (`TP·b = FP·a`).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the square root in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
