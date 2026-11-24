# ADR 0590: Cody's beta of two presence records

Status: accepted, 2026-11-23.

## Context

Cody (1975) measured the change in a community along a habitat gradient as
`β_C = (g + l)/2`, the mean of the number of kinds gained and the number lost between two
points. For two records, with `b` the kinds present only in the first and `c` those present
only in the second, the kinds lost are `b` and those gained `c`, so `β_C = (b + c)/2`. It
is a count, not a ratio: 0 for records with the same kinds, and up to the record length.

## Decision

- **The API.**
  - Python: `cody_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.CodyBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is `(b + c)/2`,
  exact in a double: a whole number or a half.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and halves the count of unshared kinds with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
