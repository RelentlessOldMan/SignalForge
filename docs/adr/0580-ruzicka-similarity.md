# ADR 0580: The Ružička similarity of two records

Status: accepted, 2026-11-22.

## Context

The Jaccard index (`jaccard_index`) and its parts (ADRs 0578, 0579) see only which kinds are
present. Ružička (1958) gave the quantitative form, `Σ min(x_i, y_i)/Σ max(x_i, y_i)`, on
the raw values: 1 for identical records, 0 for records with no kind in common, and on
presence records it is the Jaccard index. Unlike the proportional similarity (ADR 0572) it
is not scale-free: a record and its double give 1/2.

## Decision

- **The API.**
  - Python: `ruzicka_similarity(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.RuzickaSimilarity(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** Both records are divided by `m`, the larger of their two maxima, so no sum
  can overflow; then `Σ min/Σ max` is formed with the sums taken in index order. The ratio
  does not depend on `m`.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `Σ min/Σ max` with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`.
