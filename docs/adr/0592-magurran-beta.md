# ADR 0592: Magurran's beta of two presence records

Status: accepted, 2026-11-23.

## Context

Magurran (1988) gave a measure of beta diversity for two records that grows with both their
richness and their dissimilarity: `β_M = (2a + b + c)(1 − a/(a + b + c))`, the summed
richness of the two records times one less the Jaccard similarity. Here `a` is the number of
kinds present in both records and `b`, `c` those present in one only. It is a count, not a
ratio: 0 for records with the same kinds, and twice the richness for records with no kind
in common.

## Decision

- **The API.**
  - Python: `magurran_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.MagurranBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is
  `(2a + b + c)(b + c)/(a + b + c)`: an exact integer product divided once by an integer,
  so it is correctly rounded. Each record has a kind, so the denominator is never 0.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `(2a + b + c)(1 − a/(a + b + c))` with
    fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
