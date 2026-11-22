# ADR 0572: The proportional similarity

Status: accepted, 2026-11-22.

## Context

The proportional similarity of two records of resource use is the share they have in
common, `PS = Σ min(pᵢ, qᵢ)`, `pᵢ` and `qᵢ` the shares of resource `i` in each record
(Czekanowski 1909; Feinsinger, Spears and Poole 1981). It is `1 − ½ Σ |pᵢ − qᵢ|`: 1 for
proportional records, 0 when they share nothing. Unlike `bray_curtis`, which compares the
raw values, it compares shares, so the totals do not matter.

## Decision

- **The API.**
  - Python: `czekanowski_similarity(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.CzekanowskiSimilarity(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** Each record is divided by its largest value so its total cannot overflow,
  then by that total, in record order; `Σ min(pᵢ, qᵢ)` in record order, capped at 1.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator computes `Σ min(pᵢ, qᵢ)` exactly with fractions.
  - The tolerance is `abs 1e-12, rel 1e-12`.
