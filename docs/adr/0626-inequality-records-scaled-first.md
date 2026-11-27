# ADR 0626: Inequality records divided by their largest value before they are summed

Status: accepted, 2026-11-26. Amends ADRs 0510–0522.

## Context

The inequality measures of ADRs 0510–0522 are scale-free: the Gini, Theil, Hoover, Atkinson,
generalized entropy, Bonferroni, Zenga and Wolfson indices, the mean log deviation, the
coefficient of variation, the Lorenz curve, and the Palma and quintile share ratios. Each
formed a sum or a mean of the raw values, and a record whose values are each finite can sum
past the largest double. For `(1e308, 9e307, 1e300)`, all 13 gave NaN, infinity, 0, 1 or a
wrong value in both languages; the Lorenz curve came out as `(0, 0, 0, NaN)`.

## Decision

As in ADR 0625: once the values are checked, each record is divided by its largest value
when that is positive, before any sum is formed. Unlike ADR 0625, Python skips the division
instead of raising when the largest value is not positive, so each measure's own check (all
0, the median, the poorest 40% or 20%, the mean) still raises its own message. C# uses the
same `ScaledToLargest`. The coefficient of variation admits negative values, but a record
with a positive mean holds a positive value at least as large as the mean, so the quotients
lie within the record length in magnitude.

## Consequences

- Results can differ from the old ones in the last bits. Every existing vector still passes
  in both languages, within its tolerance.
- Each of the 13 generators gained an exact `huge` case on `(1e308, 9e307, 1e300)` (Atkinson
  with ε = 0.5, generalized entropy with α = 2). All 13 failed in both languages before the
  change. Mutation check: scaling by `min(top, 1)` failed the 13 in Python, and in C#, where
  one helper serves both ADRs, the 29 of ADRs 0625 and 0626.
