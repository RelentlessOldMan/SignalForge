# ADR 0460: The fifth Sokal-Sneath coefficient

Status: accepted, 2026-11-20.

## Context

The fifth of Sokal and Sneath's coefficients for two binary records is
`TP·TN / sqrt(|A|·|B|·(n − |A|)·(n − |B|))`: the geometric mean of the four conditional
probabilities of agreement whose arithmetic mean is the fourth (ADR 0459). 1 when the
records agree everywhere, 0 when no 1 or no 0 is shared.

## Decision

- **The API.**
  - Python: `sokal_sneath_v(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.SokalSneathV(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `TP·TN`, `u = |A|·|B|` and `v = (n − |A|)·(n − |B|)` are each
    converted to a double once; the value is `TP·TN / sqrt(u · v)`.
  - From 0 to 1, at most the fourth coefficient. Symmetric in the two records; unchanged
    when both records are flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant record is an error: `u · v` is then 0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, forms the square of the value in rationals
    and takes its correctly rounded square root in 40-digit decimals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
