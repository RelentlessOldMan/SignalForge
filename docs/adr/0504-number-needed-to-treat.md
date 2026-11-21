# ADR 0504: The number needed to treat

Status: accepted, 2026-11-20.

## Context

The number needed to treat is the reciprocal of the risk difference (ADR 0501): how many
records must be exposed (decision 1) for one more truth 1 than among the unexposed. Over
a common denominator it is `(TP + FP)·(FN + TN) / (TP·TN − FN·FP)`.

## Decision

- **The API.**
  - Python: `number_needed_to_treat(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.NumberNeededToTreat(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `(TP + FP)·(FN + TN)` and `TP·TN − FN·FP` are each converted to a
    double once, then one division.
  - Any real value of size at least 1; negative when the exposed share is the smaller
    (often called the number needed to harm). It changes sign when the truth is
    complemented.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A decision with no 1 or no 0 is an error, as for the risk difference.
  - A risk difference of 0 (`TP·TN = FN·FP`) is an error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and divides the two exact integers in
    40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
