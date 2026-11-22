# ADR 0575: Whittaker's beta diversity of two records

Status: accepted, 2026-11-22.

## Context

Whittaker (1960) measured how much two samples differ in which kinds they hold by
`β = S_∪/ᾱ − 1`, `S_∪` the count of kinds present in either sample and `ᾱ` the mean count
in each. For two records it is `2 S_∪/(S_x + S_y) − 1 = (b + c)/(2a + b + c)`, with `a` the
kinds present in both and `b`, `c` those in one only: 0 when both hold the same kinds, 1
when they share none. It is one less the Sørensen similarity on presence.

## Decision

- **The API.**
  - Python: `whittaker_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.WhittakerBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. With the counts `a`, `b` and
  `c`, the value is `(b + c)/(2a + b + c)`, one division of exact integers.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `2 S_∪/(S_x + S_y) − 1` with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
