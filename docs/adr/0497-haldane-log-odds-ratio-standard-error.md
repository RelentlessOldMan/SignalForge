# ADR 0497: The standard error of the Haldane log odds ratio

Status: accepted, 2026-11-20.

## Context

The Haldane log odds ratio (ADR 0494) adds a half to every cell of the table. Its
standard error is Woolf's formula (ADR 0493) on the corrected cells:
`sqrt(1/(TP + ½) + 1/(FN + ½) + 1/(FP + ½) + 1/(TN + ½))`, defined for every table.

## Decision

- **The API.**
  - Python: `haldane_log_odds_ratio_standard_error(truth, decision)` in `measurements`,
    giving a float.
  - C#: `Measurements.HaldaneLogOddsRatioStandardError(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - With `a = 2·TP + 1`, `b = 2·FN + 1`, `c = 2·FP + 1`, `d = 2·TN + 1` the sum is the
    exact rational `2·(bcd + acd + abd + abc) / (abcd)`; its numerator and denominator are
    each converted to a double once, then one division and the square root.
  - Above 0, at most `sqrt(8)`. Symmetric in the two records, and unchanged when the
    decision is complemented.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other errors: every table gives a value.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, sums the reciprocals in rationals and takes
    the square root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-15`.
