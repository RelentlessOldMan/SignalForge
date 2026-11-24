# ADR 0589: Harrison's beta of two presence records

Status: accepted, 2026-11-23.

## Context

Harrison, Ross and Lawton (1992) modified Whittaker's beta (ADR 0575) so that it is not
driven by a difference in richness: `β_H2 = (γ/α_max − 1)/(N − 1)`, with `γ` the number of
kinds in all `N` records together and `α_max` the richness of the richest record. For two
records `N − 1 = 1`, and with `a` the kinds present in both and `b`, `c` those present in
one only, `γ = a + b + c` and `α_max = a + max(b, c)`, so
`β_H2 = min(b, c)/(a + max(b, c))`. It is 0 for nested records and 1 for records of equal
richness with no kind in common.

## Decision

- **The API.**
  - Python: `harrison_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.HarrisonBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is
  `min(b, c)/(a + max(b, c))`, one division of exact integers; each record has a kind, so
  the denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `γ/α_max − 1` with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
