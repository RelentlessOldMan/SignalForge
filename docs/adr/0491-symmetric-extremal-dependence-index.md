# ADR 0491: The symmetric extremal dependence index

Status: accepted, 2026-11-20.

## Context

The symmetric extremal dependence index of a binary forecast against a binary truth is
`(ln F − ln H − ln(1 − F) + ln(1 − H)) / (ln F + ln H + ln(1 − F) + ln(1 − H))`, with the
hit rate `H = TP / |A|` and the false alarm rate `F = FP / (n − |A|)`. It is the
extremal dependence index (ADR 0490) made symmetric: complementing both records swaps `H`
with `1 − F` and leaves the value unchanged. With every cell non-zero, each logarithm is
below 0 and the value is from −1 to 1; 0 when `H = F`.

## Decision

- **The API.**
  - Python: `symmetric_extremal_dependence_index(truth, decision)` in `measurements`,
    giving a float.
  - C#: `Measurements.SymmetricExtremalDependenceIndex(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `ln F = ln(FP / (n − |A|))`, `ln(1 − F) = ln(TN / (n − |A|))`, `ln H = ln(TP / |A|)`
    and `ln(1 − H) = ln(FN / |A|)`, each the natural logarithm of one division of two
    counts, each converted to a double once; then the numerator and the denominator summed
    left to right, and one division.
  - From −1 to 1. Not symmetric in the records: `truth` gives the rows.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Any cell of the table equal to 0 is an error (the logarithm of 0); this covers a
    constant record.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the logarithms in 40-digit decimals.
  - The tolerance is `abs 1e-13, rel 1e-13`.
