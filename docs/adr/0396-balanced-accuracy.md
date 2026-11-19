# ADR 0396: The balanced accuracy

Status: accepted, 2026-11-19.

## Context

Plain accuracy rewards a detector that always says the common class. The balanced accuracy
(Brodersen and others, 2010) averages the rate of correct decisions within each true class,
so chance scores 1/2 whatever the prevalence. It is `(J + 1)/2`, J being Youden's J
(ADR 0387).

## Decision

- **The API.**
  - Python: `balanced_accuracy(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.BalancedAccuracy(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
  - The records as for the Matthews correlation (ADR 0385): 0 and 1, 1 positive.
  - Only the binary form is built; the mean recall over several classes is not.
- **The value.**
  - `BA = (TP·(TN + FP) + TN·(TP + FN))/(2·(TP + FN)·(TN + FP))`, the same as
    `(TP/(TP + FN) + TN/(TN + FP))/2`, from 0 to 1. Numerator and denominator are whole
    numbers, each converted to `double`, then one division.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1, every value 0 or 1.
  - `TP + FN > 0` and `TN + FP > 0`: the truth holds both a 1 and a 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts in integers and averages exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
