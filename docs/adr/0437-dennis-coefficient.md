# ADR 0437: The Dennis coefficient

Status: accepted, 2026-11-19.

## Context

The Dennis coefficient of two binary records is `(TP·TN − FN·FP) / √(n·|A|·|B|)`. Since
`TP·TN − FN·FP = n·TP − |A|·|B|`, it is the excess of the shared 1s over the number chance
expects, `|A|·|B| / n`, measured in units of the square root of that number: a z-like
score for the overlap. 0 for no association; it has no fixed bound and grows with `√n`.

## Decision

- **The API.**
  - Python: `dennis_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.DennisCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `TP·TN − FN·FP` and `n·|A|·|B|` exact integers, each converted to a double once
    (correctly rounded in both languages), then a correctly rounded square root of the
    second and one division.
  - Symmetric; its sign is that of Yule's Q.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - Either record with no 1 is an error: the denominator is zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes the root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
