# ADR 0579: The nestedness part of the Jaccard dissimilarity

Status: accepted, 2026-11-22.

## Context

Baselga (2012) split the Jaccard dissimilarity of two presence records,
`β_jac = (b + c)/(a + b + c)`, into the turnover part `β_jtu` (ADR 0578) and the rest, the
part due to nestedness: `β_jne = β_jac − β_jtu = (|b − c|/(a + b + c))·(a/(a + 2 min(b, c)))`,
with `a` the kinds present in both records and `b`, `c` those present in one only. It is 0
when the records hold equally many kinds of their own or share none.

## Decision

- **The API.**
  - Python: `jaccard_nestedness(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.JaccardNestedness(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The product form
  `|b − c|·a/((a + b + c)(a + 2 min(b, c)))` is one division of exact integers, so the value
  is correctly rounded, as in ADR 0577.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `β_jac − β_jtu` with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
