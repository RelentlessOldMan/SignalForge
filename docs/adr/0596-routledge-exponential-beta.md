# ADR 0596: Routledge's exponential beta of two presence records

Status: accepted, 2026-11-23.

## Context

Routledge (1977) also gave the exponential form of his information measure (ADR 0595):
`β-E = exp(β-I) − 1`, as listed by Koleff, Gaston and Lennon (2003). With `a` the number of
kinds present in both records, `b`, `c` those present in one only, `p = a + b`, `q = a + c`
and `n = p + q`, it is `n/(2^(2a/n) p^(p/n) q^(q/n)) − 1`. It is 0 when the records have the
same kinds and 1 when they share nothing and have the same richness, its largest value.

## Decision

- **The API.**
  - Python: `routledge_exponential_beta(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.RoutledgeExponentialBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** `exp(β-I) − 1`, with `β-I` computed as in ADR 0595 (held at 0 from below),
  so the value is held at 0 from below too.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator counts presences and forms the value with 60-digit decimal logarithms and
    exponentials.
  - Each hand case is also checked against its closed form in powers of 2, 3, 5 and 7.
  - The tolerance is `abs 1e-14, rel 1e-14`.
