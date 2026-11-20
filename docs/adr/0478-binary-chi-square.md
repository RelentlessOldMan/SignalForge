# ADR 0478: The chi-square statistic of two binary records

Status: accepted, 2026-11-20.

## Context

Pearson's chi-square statistic of the 2x2 table of two binary records, without continuity
correction, is `n·(TP·TN − FN·FP)² / (|A|·|B|·(n − |A|)·(n − |B|))`: `n` times the square
of the phi coefficient. 0 when the records are independent, `n` when they are equal or
opposite.

## Decision

- **The API.**
  - Python: `binary_chi_square(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.BinaryChiSquare(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `phi = k / sqrt(u · v)` with `k = TP·TN − FN·FP`, `u = |A|·|B|` and
    `v = (n − |A|)·(n − |B|)`, each exact integer converted to a double once; then
    `n · phi · phi`, multiplied left to right. Squaring the integer `k` first could overflow
    64 bits.
  - From 0 to `n`. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant record is an error: `u · v` is then 0.
  - No continuity correction.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
