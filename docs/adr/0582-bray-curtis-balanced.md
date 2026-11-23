# ADR 0582: The balanced-variation part of the Bray–Curtis dissimilarity

Status: accepted, 2026-11-23.

## Context

Baselga (2013) carried the turnover and nestedness split of ADRs 0576 and 0577 over to
abundances. With `A = Σ min(x_i, y_i)` the amount the two records share and `B`, `C` the
amounts only one holds (`B = Σ x_i − A`, `C = Σ y_i − A`), the Bray–Curtis dissimilarity
`(B + C)/(2A + B + C)` splits into balanced variation, `β_bal = min(B, C)/(A + min(B, C))`,
where some kinds gain what others lose, and an abundance gradient, the rest. `β_bal` is 0
when one record is at least the other kind by kind and 1 when they share nothing.

## Decision

- **The API.**
  - Python: `bray_curtis_balanced(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.BrayCurtisBalanced(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** Both records are divided by `m`, the larger of their two maxima, as in
  ADR 0580. In index order, `A` sums `min(x_i, y_i)/m`, `B` sums `(x_i − min(x_i, y_i))/m`
  and `C` sums `(y_i − min(x_i, y_i))/m`, so `B` and `C` never come from a cancelling
  difference of totals. The value is `min(B, C)/(A + min(B, C))`; each record has a value
  above 0, so the denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms `A`, `B`, `C` and the ratio with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`.
