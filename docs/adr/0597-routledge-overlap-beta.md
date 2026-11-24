# ADR 0597: Routledge's overlap beta of two presence records

Status: accepted, 2026-11-23.

## Context

Routledge (1977) counted, over the pooled kinds `S`, the pairs of kinds whose occurrences
overlap, `r`, and set `β-R = S²/(2r + S) − 1`. For two records, as listed by Koleff, Gaston
and Lennon (2003), with `a` the number of kinds present in both and `b`, `c` those present in
one only, `S = a + b + c` and the pairs that do not overlap are the `bc` pairs of one kind
from each record's own part, so `2r + S = S² − 2bc` and

`β-R = 2bc/((a + b + c)² − 2bc)`.

It is 0 when one record's kinds contain the other's, and 1 when the records share nothing
and have the same richness, its largest value.

## Decision

- **The API.**
  - Python: `routledge_overlap_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.RoutledgeOverlapBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** A kind is present when its value is above 0. The value is
  `2bc/((a + b + c)² − 2bc)`, one division of exact integers. Since `2bc ≤ (b + c)²/2`, the
  denominator is at least `S²/2`, which is at least 1/2 since each record has a kind.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms `S²/(2r + S) − 1` with fractions, counting the
    overlapping pairs `r` directly.
  - The tolerance is `abs 1e-15, rel 1e-15`.
