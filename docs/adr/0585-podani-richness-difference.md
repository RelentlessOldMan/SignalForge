# ADR 0585: Podani's richness-difference part of the Jaccard dissimilarity

Status: accepted, 2026-11-23.

## Context

Podani and Schmera (2011) split the Jaccard dissimilarity `(b + c)/(a + b + c)` into
replacement (ADR 0584) and richness difference, `|b − c|/(a + b + c)`, the share of the
kinds in either record that one record has in excess of the other. Here `a` is the number
of kinds present in both records and `b`, `c` those present in one only. It is 0 for
records of equal richness and rises to `1 − 1/S` when one record holds a single kind of the
other's `S`.

## Decision

- **The API.**
  - Python: `podani_richness_difference(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.PodaniRichnessDifference(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is
  `|b − c|/(a + b + c)`, one division of exact integers; each record has a kind, so the
  denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms the ratio with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
