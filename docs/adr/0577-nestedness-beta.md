# ADR 0577: The nestedness part of the Sørensen dissimilarity

Status: accepted, 2026-11-22.

## Context

Baselga (2010) split the Sørensen dissimilarity of two records, which is Whittaker's beta
(ADR 0575), into turnover, Simpson's beta (ADR 0576), and the rest, the part due to
nestedness: `β_nes = β_sor − β_sim = (|b − c|/(2a + b + c))·(a/(a + min(b, c)))`, with
`a` the kinds present in both records and `b`, `c` those present in one only. It is 0 when
the records hold equally many kinds of their own or share none, and grows as the poorer
record becomes a subset of the richer one.

## Decision

- **The API.**
  - Python: `nestedness_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.NestednessBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The product form
  `|b − c|·a/((2a + b + c)(a + min(b, c)))` is one division of exact integers, so the value
  is correctly rounded; the difference of the two betas would round twice.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `β_sor − β_sim` with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
