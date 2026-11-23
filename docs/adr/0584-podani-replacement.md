# ADR 0584: Podani's replacement part of the Jaccard dissimilarity

Status: accepted, 2026-11-23.

## Context

Baselga's split of the Jaccard dissimilarity (ADRs 0578, 0579) scales turnover by
`a + 2 min(b, c)`. Podani and Schmera (2011) split the same dissimilarity
`(b + c)/(a + b + c)` additively over one denominator instead: replacement,
`2 min(b, c)/(a + b + c)`, the kinds swapped one for one, and richness difference,
`|b − c|/(a + b + c)`, the kinds one record has in excess. Here `a` is the number of kinds
present in both records and `b`, `c` those present in one only. The replacement part is 0
for nested records and 1 for records of equal richness with no kind in common.

## Decision

- **The API.**
  - Python: `podani_replacement(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.PodaniReplacement(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is
  `2 min(b, c)/(a + b + c)`, one division of exact integers; each record has a kind, so the
  denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms the ratio with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
