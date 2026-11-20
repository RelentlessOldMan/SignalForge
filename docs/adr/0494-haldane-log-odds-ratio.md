# ADR 0494: The Haldane log odds ratio

Status: accepted, 2026-11-20.

## Context

The log odds ratio (ADR 0480) is undefined when any cell of the table is 0. Haldane's
correction adds a half to every cell first: `ln((TP + ½)(TN + ½) / ((FN + ½)(FP + ½)))`.
It is defined for every table, 0 when the four cells are equal, and changes sign when the
decision is complemented.

## Decision

- **The API.**
  - Python: `haldane_log_odds_ratio(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.HaldaneLogOddsRatio(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Doubling every corrected cell leaves the ratio unchanged, so it is formed from the
    exact integers `(2·TP + 1)(2·TN + 1)` and `(2·FN + 1)(2·FP + 1)`, each converted to a
    double once; then one division and the natural logarithm.
  - Any real value. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other errors: every table gives a value.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the logarithm in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
