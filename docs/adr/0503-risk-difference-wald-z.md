# ADR 0503: The Wald z of the risk difference

Status: accepted, 2026-11-20.

## Context

The Wald statistic for a difference of two proportions divides the risk difference
(ADR 0501) by its unpooled standard error (ADR 0502).

## Decision

- **The API.**
  - Python: `risk_difference_wald_z(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.RiskDifferenceWaldZ(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The risk difference is formed as in ADR 0501 and the squared standard error as in
    ADR 0502 (the two terms each an exact integer over an exact integer); the risk
    difference is divided by the square root of the squared standard error.
  - Any real value; 0 when the two shares are equal. It changes sign when the truth is
    complemented.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A decision with no 1 or no 0 is an error, as for the risk difference.
  - A standard error of 0 (`TP·FP = 0` and `FN·TN = 0`) is an error.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, forms both parts in rationals and takes the
    square root in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
