# ADR 0386: The F1 score

Status: accepted, 2026-11-19.

## Context

The F1 score (van Rijsbergen's F measure with equal weights) scores a binary decision by the
harmonic mean of its precision `TP/(TP + FP)` and recall `TP/(TP + FN)`. It ignores the true
negatives, which suits detection where the negatives are an uncounted background.

## Decision

- **The API.**
  - Python: `f1_score(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.F1Score(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
  - The records as for the Matthews correlation (ADR 0385): 0 and 1, 1 positive.
- **The value.**
  - `F1 = 2TP/(2TP + FP + FN)`, from 0 to 1, a ratio of whole numbers. It equals the
    harmonic mean of precision and recall whenever both are defined, and is still defined
    when one of them is not (`TP = 0` with some `FP` or `FN` gives 0).
- **The rules.**
  - Both records one-dimensional, the same length, at least 1, every value 0 or 1.
  - `2TP + FP + FN > 0`: at least one positive in either record.

## Consequences

- The cost is one pass.
- The F-beta family with other weights is not built.
- **Vectors.**
  - The generator counts in integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
