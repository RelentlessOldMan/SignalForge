# ADR 0395: Markedness

Status: accepted, 2026-11-19.

## Context

Powers (2011) named two chance-corrected measures of a binary decision. Informedness is
Youden's J (ADR 0387), the sensitivity and specificity less 1; markedness is its dual over the
decisions, the precision and the negative predictive value less 1. Their geometric mean is the
magnitude of the Matthews correlation (ADR 0385).

## Decision

- **The API.**
  - Python: `markedness(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.Markedness(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
  - The records as for the Matthews correlation: 0 and 1, 1 positive.
- **The value.**
  - `MK = (TP·TN − FP·FN)/((TP + FP)(TN + FN))`, the same as
    `TP/(TP + FP) + TN/(TN + FN) − 1`, from −1 to 1. The single fraction is used: its
    numerator and denominator are whole numbers, each converted to `double`, then one division.
  - It is Youden's J with truth and decision swapped.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1, every value 0 or 1.
  - `TP + FP > 0` and `TN + FN > 0`: the decision holds both a 1 and a 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts in integers and divides exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
