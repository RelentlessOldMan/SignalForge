# ADR 0583: The abundance-gradient part of the Bray–Curtis dissimilarity

Status: accepted, 2026-11-23.

## Context

Baselga (2013) split the Bray–Curtis dissimilarity `(B + C)/(2A + B + C)` into balanced
variation (ADR 0582) and the rest, the part due to an abundance gradient:
`β_gra = β_bc − β_bal = (|B − C|/(2A + B + C))·(A/(A + min(B, C)))`, with `A` the amount the
two records share and `B`, `C` the amounts only one holds. It is 0 when the records hold
equal unshared amounts or share nothing, and grows as one record becomes a scaled-down
copy of the other.

## Decision

- **The API.**
  - Python: `bray_curtis_gradient(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.BrayCurtisGradient(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** `A`, `B` and `C` are formed as in ADR 0582. The value is the product form
  `|B − C|·A/((2A + B + C)(A + min(B, C)))`, not the difference of the two dissimilarities,
  which would cancel when the gradient part is small.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `β_bc − β_bal` with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`.
