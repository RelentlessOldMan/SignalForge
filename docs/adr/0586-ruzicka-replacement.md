# ADR 0586: The replacement part of the Ružička dissimilarity

Status: accepted, 2026-11-23.

## Context

The Ružička dissimilarity `(B + C)/(A + B + C)`, one less the Ružička similarity (ADR 0580),
is the quantitative form of the Jaccard dissimilarity, with `A = Σ min(xᵢ, yᵢ)` the amount
the two records share and `B = Σ xᵢ − A`, `C = Σ yᵢ − A` the amounts only one holds.
Legendre (2014) split it as Podani split the Jaccard dissimilarity (ADRs 0584, 0585):
replacement `2 min(B, C)/(A + B + C)` and abundance difference `|B − C|/(A + B + C)`. On
presence records the replacement part is Podani's.

## Decision

- **The API.**
  - Python: `ruzicka_replacement(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.RuzickaReplacement(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** `A`, `B` and `C` are summed in index order after dividing every value by the
  largest value in either record, as in ADR 0582, so that no sum overflows. The value is
  `2 min(B, C)/(A + (B + C))`, with `B + C` added first so that swapping the records gives
  the same double.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `A`, `B`, `C` and the ratio with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`.
