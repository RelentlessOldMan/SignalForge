# ADR 0594: Lennon's gradient beta of two presence records

Status: accepted, 2026-11-23.

## Context

Lennon et al. (2001) separated the part of beta diversity that comes from a gradient in
richness: `β-gl = 2|b − c|/(2a + b + c)` (the form listed by Koleff, Gaston and Lennon
2003). Here `a` is the number of kinds present in both records and `b`, `c` those present
in one only. It is 0 when the records gain and lose the same number of kinds, and grows
with the difference in their richness, `|b − c|`, over their summed richness. Since each
record has a kind, it stays below 2.

## Decision

- **The API.**
  - Python: `lennon_gradient_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.LennonGradientBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is
  `2|b − c|/(2a + b + c)`, one division of exact integers; each record has a kind, so the
  denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `2|b − c|/(2a + b + c)` with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
