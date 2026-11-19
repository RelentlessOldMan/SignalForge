# ADR 0384: Scott's pi

Status: accepted, 2026-11-19.

## Context

Scott (1955) corrected the agreement of two raters for chance before Cohen did, but took the
chance rates from both raters' labels pooled, as if the two drew from one distribution.
It is Fleiss' kappa (ADR 0382) for two raters, and differs from Cohen's kappa (ADR 0383) only
when the raters use the categories at different rates.

## Decision

- **The API.**
  - Python: `scott_pi(a, b)` in `measurements`, giving a float.
  - C#: `Measurements.ScottPi(ReadOnlySpan<double> a, ReadOnlySpan<double> b)`.
  - Labels as for Cohen's kappa: numbers, the categories the distinct values compared with
    `==`.
- **The value.**
  - `A` is the number of items with `a_i = b_i`, `a_c` and `b_c` the counts of category `c`,
    and `F = Σ_c (a_c + b_c)²`.
  - `π_c = (a_c + b_c)/(2N)`, `p_e = Σ_c π_c² = F/(4N²)`, `p_o = A/N`.
  - `π = (p_o − p_e)/(1 − p_e) = (4NA − F)/(4N² − F)`, a ratio of whole numbers, computed in
    that form.
- **The rules.**
  - `a` and `b` real, one-dimensional, finite and the same length, at least 1.
  - `p_e < 1`: not every label in both records the same.

## Consequences

- The cost is a sort of each record.
- The tests check it against Fleiss' kappa with two ratings per item.
- **Vectors.**
  - The generator counts in integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
