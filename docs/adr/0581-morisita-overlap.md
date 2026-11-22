# ADR 0581: Morisita's overlap of two count records

Status: accepted, 2026-11-22.

## Context

The Morisita–Horn overlap (ADR 0573) uses the plain Simpson concentration `Σ p²` of each
record. Morisita (1959) used the unbiased one for counts, `λ = Σ n_i(n_i − 1)/(N(N − 1))`,
which gives `C = 2 Σ x_i y_i/((λ_x + λ_y) X Y)`, with `X` and `Y` the two totals. It is 0
for records with no kind in common and near 1 for records drawn from the same shares; on
small samples it can exceed 1 (two records of `[5, 5]` give 9/8).

## Decision

- **The API.**
  - Python: `morisita_overlap(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.MorisitaOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** With `S_x = Σ x_i(x_i − 1)` and `S_y` likewise, the value is
  `2 Σ x_i y_i (X − 1)(Y − 1)/(S_x Y(Y − 1) + S_y X(X − 1))`. Every sum is an exact integer
  below 2^53 under the total limit; the products and the division are formed in the same
  order in both languages.
- **The rules.** Each record one-dimensional, real, finite, whole numbers at least 0, not
  empty, totalling from 2 to 10 000 000; the same length; and `S_x + S_y` above 0 (some
  count above 1), else the denominator is 0. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the value with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`.
