# ADR 0508: The Wald z of Cohen's h

Status: accepted, 2026-11-20.

## Context

Cohen's h (ADR 0506) over its large-sample standard error (ADR 0507) is the arcsine test
of two proportions: approximately standard normal when the two shares are equal.

## Decision

- **The API.**
  - Python: `cohen_h_wald_z(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.CohenHWaldZ(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Cohen's h is formed as in ADR 0506 and the squared standard error as in ADR 0507
    (the exact integer `N` over the exact integer `(TP + FP)·(FN + TN)`); h is divided by
    the square root of the squared standard error.
  - Any real value; 0 when the two shares are equal. It changes sign when the truth is
    complemented.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A decision with no 1 or no 0 is an error, as for Cohen's h. The standard error is
    then never 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, takes each arctangent of an exact square
    root in 50-digit decimals, by argument halving and the Taylor series, and divides by
    the square root of the exact ratio.
  - The tolerance is `abs 1e-14, rel 1e-14`.
