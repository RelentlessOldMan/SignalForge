# ADR 0481: The G statistic of two binary records

Status: accepted, 2026-11-20.

## Context

The G statistic (the log-likelihood ratio statistic) of the 2x2 table of two binary
records is `2·Σ cell·ln(n·cell / (row·column))` over the nonzero cells: `2n` times their
mutual information in nats (ADR 0464). 0 when the records are independent.

## Decision

- **The API.**
  - Python: `binary_g_statistic(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.BinaryGStatistic(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Each nonzero cell `c` with row total `r` and column total `k` adds
    `c · ln(n·c / (r·k))`, the exact integers `c`, `n·c` and `r·k` each converted to a
    double once. The cells are added in the order TP, FN, FP, TN, as for the mutual
    information; the sum is then doubled.
  - At least 0 in exact arithmetic; rounding can leave a value a few ulps below 0 near
    independence, and it is not clamped. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Constant records are allowed: their statistic is 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and sums the terms in 40-digit decimals, each
    log of an exact rational correctly rounded.
  - The tolerance is `abs 1e-13, rel 1e-13`.
