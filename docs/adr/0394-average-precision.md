# ADR 0394: The average precision

Status: accepted, 2026-11-19.

## Context

The average precision summarises the precision–recall curve of a real-valued score: the
precision at each threshold, weighted by the recall gained there. It suits rare positives,
where the ROC AUC (ADR 0393) can look good while precision is poor.

## Decision

- **The API.**
  - Python: `average_precision(truth, score)` in `measurements`, giving a float.
  - C#: `Measurements.AveragePrecision(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> score)`.
  - The records as for the ROC AUC.
- **The value.**
  - The distinct scores, taken from the highest down, are the thresholds. At threshold `τ`,
    `Dτ` items score at least `τ`, `Tτ` of them positive, and `kτ` positives score exactly `τ`.
  - `AP = (1/n₁)·Σ kτ·Tτ/Dτ`: the step sum, no interpolation. Tied scores are one threshold,
    so the value does not depend on the order of ties.
  - Each term is `kτ·Tτ` in integers, converted to `double` and divided by `Dτ`; the terms are
    summed from the highest threshold down, then divided by `n₁`.
  - From above 0 up to 1; 1 when every positive outscores every negative.
- **The rules.**
  - Both records one-dimensional, the same length.
  - Every truth 0 or 1; every score finite.
  - At least one positive. Negatives are not needed: with none, `AP = 1`.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator forms the sum exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`, for a sum in order against the exact one.
