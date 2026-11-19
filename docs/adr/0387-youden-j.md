# ADR 0387: Youden's J

Status: accepted, 2026-11-19.

## Context

Youden (1950) summarised a binary test by its sensitivity plus its specificity less 1, the
informedness: 0 for a test no better than chance, 1 for a perfect one. Unlike accuracy it
does not depend on how common the positives are. On a ROC plot it is the height of the
operating point above the diagonal.

## Decision

- **The API.**
  - Python: `youden_j(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.YoudenJ(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
  - The records as for the Matthews correlation (ADR 0385): 0 and 1, 1 positive.
- **The value.**
  - `J = TP/(TP + FN) + TN/(TN + FP) − 1 = (TP·TN − FP·FN)/((TP + FN)(TN + FP))`, from −1
    to 1. The second form is a ratio of whole numbers and is the one computed.
  - It is not symmetric: swapping truth and decision gives the markedness instead.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1, every value 0 or 1.
  - Both classes present in the truth.

## Consequences

- The cost is one pass.
- The balanced accuracy is `(J + 1)/2` and is not built separately.
- **Vectors.**
  - The generator counts in integers and checks the two forms agree exactly.
  - The tolerance is `abs 1e-15, rel 1e-15`.
