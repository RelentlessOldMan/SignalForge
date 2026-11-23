# ADR 0587: The richness-difference part of the Ružička dissimilarity

Status: accepted, 2026-11-23.

## Context

Legendre (2014) split the Ružička dissimilarity `(B + C)/(A + B + C)` into replacement
(ADR 0586) and abundance difference, `|B − C|/(A + B + C)`, the share of the total held in
excess by the larger record. Here `A = Σ min(xᵢ, yᵢ)` and `B = Σ xᵢ − A`, `C = Σ yᵢ − A`.
On presence records it is Podani's richness difference (ADR 0585). It is 0 for records of
equal totals and approaches 1 as one record's total dwarfs the other's.

## Decision

- **The API.**
  - Python: `ruzicka_richness_difference(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.RuzickaRichnessDifference(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** `A`, `B` and `C` are summed as in ADR 0586. The value is
  `|B − C|/(A + (B + C))`, the same double for either order of the records.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `A`, `B`, `C` and the ratio with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`.
