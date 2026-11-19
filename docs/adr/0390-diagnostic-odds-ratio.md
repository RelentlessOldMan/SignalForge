# ADR 0390: The diagnostic odds ratio

Status: accepted, 2026-11-19.

## Context

Glas and others (2003) summarised a binary test by one number: the odds of a positive
decision among the true positives over the odds among the true negatives. It does not
depend on prevalence, and its logarithm is the usual pooled quantity in meta-analysis.

## Decision

- **The API.**
  - Python: `diagnostic_odds_ratio(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.DiagnosticOddsRatio(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
  - The records as for the Matthews correlation (ADR 0385): 0 and 1, 1 positive.
- **The value.**
  - `DOR = (TP·TN)/(FP·FN)`, from 0 up; 1 for a test no better than chance.
  - Both products are whole numbers. Each is converted to `double` and one division done,
    so the value is the correctly rounded ratio while the products stay below `2⁵³`.
  - No continuity correction is added. A caller who wants the Haldane correction adds 0.5
    to each cell itself; it would not fit records of 0 and 1.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1, every value 0 or 1.
  - `FP > 0` and `FN > 0`: with either 0 the ratio is infinite or undefined.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts in integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
