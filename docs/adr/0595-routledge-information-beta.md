# ADR 0595: Routledge's information beta of two presence records

Status: accepted, 2026-11-23.

## Context

Routledge (1977) gave an information measure of the beta diversity of records. For two
records, as listed by Koleff, Gaston and Lennon (2003), with `a` the number of kinds present
in both and `b`, `c` those present in one only, it is

`β-I = ln(2a + b + c) − (2a ln 2 + (a + b) ln(a + b) + (a + c) ln(a + c))/(2a + b + c)`.

It is the Shannon information of the pooled presences less the mean information of the two
records: 0 when the records have the same kinds, and at most `ln 2`, reached when they share
nothing and have the same richness.

## Decision

- **The API.**
  - Python: `routledge_information_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.RoutledgeInformationBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. With `p = a + b`, `q = a + c`
  and `n = p + q`, the value is `ln n − (2a ln 2 + (p ln p + q ln q))/n`, with the natural
  logarithm. The bracket keeps the sum symmetric in the records. Each record has a kind, so
  `p`, `q` and `n` are at least 1. Rounding can leave a value a few units below 0 when the
  records have the same kinds; the result is held at 0 from below.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms the value with 60-digit decimal logarithms.
  - Each hand case is also checked against its closed form in `ln 2`, `ln 3`, `ln 5`, `ln 7`.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the cancellation between the logarithms.
