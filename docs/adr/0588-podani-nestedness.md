# ADR 0588: Podani's nestedness of two presence records

Status: accepted, 2026-11-23.

## Context

Podani and Schmera (2012) measure how far one record's kinds are a subset of the other's
as `N = (a + |b − c|)/(a + b + c)` when the records share a kind, and `N = 0` when they share
none, since records with nothing in common are not nested at all. Here `a` is the number of
kinds present in both records and `b`, `c` those present in one only. When `a > 0` it is
one less Podani's replacement part (ADR 0584); it is 1 when one record's kinds lie within
the other's.

## Decision

- **The API.**
  - Python: `podani_nestedness(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.PodaniNestedness(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is 0 when `a = 0`,
  else `(a + |b − c|)/(a + b + c)`, one division of exact integers.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms the ratio with fractions.
  - The tolerance is `abs 1e-15, rel 1e-15`.
