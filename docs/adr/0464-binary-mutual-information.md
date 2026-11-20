# ADR 0464: The mutual information of two binary records

Status: accepted, 2026-11-20.

## Context

The mutual information of two binary records is the mutual information of their 2x2 table:
`Σ (cell/n)·ln(n·cell / (row·column))` over the four cells, an empty cell giving 0. It is
in nats, 0 when the records are independent, and at most the entropy of either record.
`auto_mutual_information` is a different measure, of one real signal against itself.

## Decision

- **The API.**
  - Python: `binary_mutual_information(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.BinaryMutualInformation(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The cells in the order TP, FN, FP, TN, each with its truth margin and decision margin.
    For a nonzero cell `c` with margins `r` and `k`, the term is `c/n` times the platform's
    natural `log` of `n·c / (r·k)`, each exact integer converted to a double once. The
    terms are summed in that order starting from 0.
  - `log` is not correctly rounded, and the terms may cancel, so the two languages may
    differ in the last few bits; near independence the value may come out a rounding error
    below 0.
  - Symmetric in the two records; unchanged when either record is flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No other error: a constant record gives 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and sums the four terms in 40-digit decimals,
    each logarithm correctly rounded there.
  - The tolerance is `abs 1e-15, rel 1e-13`.
