# ADR 0593: Williams' beta of two presence records

Status: accepted, 2026-11-23.

## Context

Williams (1996) measured the turnover between two records, apart from any difference in
their richness, as `β-3 = min(b, c)/(a + b + c)` (the form listed by Koleff, Gaston and
Lennon 2003). Here `a` is the number of kinds present in both records and `b`, `c` those
present in one only. It is 0 when one record's kinds contain the other's and at most 1/2,
reached when the records share nothing and have the same richness. It is half Podani's
replacement (ADR 0584).

## Decision

- **The API.**
  - Python: `williams_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.WilliamsBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is
  `min(b, c)/(a + b + c)`, one division of exact integers; each record has a kind, so the
  denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `min(b, c)/(a + b + c)` with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
