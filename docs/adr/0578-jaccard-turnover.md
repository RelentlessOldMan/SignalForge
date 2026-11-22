# ADR 0578: The turnover part of the Jaccard dissimilarity

Status: accepted, 2026-11-22.

## Context

Baselga (2012) split the Jaccard dissimilarity of two presence records,
`β_jac = (b + c)/(a + b + c)`, the way ADR 0577 split the Sørensen one: a turnover part
`β_jtu = 2 min(b, c)/(a + 2 min(b, c))` and a nestedness part `β_jac − β_jtu`. Here `a` is
the number of kinds present in both records and `b`, `c` those present in one only. The
turnover part is 0 when one record's kinds are a subset of the other's and 1 when they
share none; it is never below Simpson's beta (ADR 0576).

## Decision

- **The API.**
  - Python: `jaccard_turnover(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.JaccardTurnover(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. With the counts `a`, `b` and
  `c`, the value is `2 min(b, c)/(a + 2 min(b, c))`, one division of exact integers. Each
  record has a kind, so `a = 0` forces `min(b, c) ≥ 1` and the denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms the ratio with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
