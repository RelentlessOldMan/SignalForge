# ADR 0576: Simpson's beta of two records

Status: accepted, 2026-11-22.

## Context

Whittaker's beta (ADR 0575) is positive whenever one record holds kinds the other lacks,
even when the poorer record's kinds are all in the richer one. Lennon et al. (2001)
measured turnover alone with Simpson's dissimilarity, `β_sim = min(b, c)/(a + min(b, c))`,
`a` the kinds present in both records and `b`, `c` those present in one only. It is 0 when
one record's kinds are a subset of the other's and 1 when they share none.

## Decision

- **The API.**
  - Python: `simpson_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.SimpsonBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. With the counts `a`, `b` and
  `c`, the value is `min(b, c)/(a + min(b, c))`, one division of exact integers. Each record
  has a kind, so `a = 0` forces `min(b, c) ≥ 1` and the denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms the ratio with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
