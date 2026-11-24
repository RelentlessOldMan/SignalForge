# ADR 0591: Wilson and Shmida's beta of two presence records

Status: accepted, 2026-11-23.

## Context

Wilson and Shmida (1984) measured turnover along a gradient as
`β_T = (g + l)/(2ᾱ)`: the kinds gained plus the kinds lost, over twice the mean richness
of the records. For two records, with `a` the kinds present in both and `b`, `c` those
present in one only, `g + l = b + c` and `2ᾱ = 2a + b + c`, so `β_T = (b + c)/(2a + b + c)`.
Cody's beta (ADR 0590) is the same count of changes without the scaling. On presence
records it equals the Bray–Curtis dissimilarity of the 0/1 records.

## Decision

- **The API.**
  - Python: `wilson_shmida_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.WilsonShmidaBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is
  `(b + c)/(2a + b + c)`, one division of exact integers; each record has a kind, so the
  denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `(g + l)/(2ᾱ)` with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
