# ADR 0385: The Matthews correlation coefficient

Status: accepted, 2026-11-19.

## Context

Matthews (1975) scored a binary decision against the truth with the Pearson correlation of
the two 0/1 records, the phi coefficient of their 2 × 2 table. Unlike the error rate it
stays informative when one class is rare, which is the usual case for a detector.

## Decision

- **The API.**
  - Python: `matthews_correlation(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.MatthewsCorrelation(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
  - The records hold 0 and 1 only, as `double`, like the bit records elsewhere; 1 is the
    positive class.
- **The value.**
  - `TP`, `TN`, `FP`, `FN` count the items with truth and decision (1, 1), (0, 0), (0, 1)
    and (1, 0).
  - `MCC = (TP·TN − FP·FN)/√((TP + FP)(TP + FN)(TN + FP)(TN + FN))`, from −1 to 1.
  - The numerator is a whole number. The product under the root is formed in `double` in
    the order written, then the root is taken, then the division is done.
  - It is symmetric: swapping truth and decision gives the same value.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1, every value 0 or 1.
  - Every factor under the root positive: both classes present in both records. With a
    class missing the correlation is undefined, and it is an error rather than a chosen 0.

## Consequences

- The cost is one pass.
- The tests check it against the Pearson correlation (ADR 0368) of the two records.
- **Vectors.**
  - The generator counts in integers and takes one correctly rounded root of the exact
    product.
  - The tolerance is `abs 1e-15, rel 1e-14`.
