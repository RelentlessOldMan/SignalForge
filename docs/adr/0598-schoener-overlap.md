# ADR 0598: Schoener's overlap of two records

Status: accepted, 2026-11-23.

## Context

Schoener (1970) measured how much two records of the use of the same kinds overlap as the
shared part of their shares: with `p_i = x_i/Σx` and `q_i = y_i/Σy`,
`C = 1 − ½ Σ|p_i − q_i| = Σ min(p_i, q_i)`. It is 1 when the records are proportional and 0
when no kind is used by both. It is one less the Bray–Curtis dissimilarity of the shares.

Peirce's skill score had been listed next; it is Youden's J (`youden_j`), already built, so
it was dropped.

## Decision

- **The API.**
  - Python: `schoener_overlap(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.SchoenerOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** Each record is first divided by its largest value, so its sum cannot
  overflow. With `s_x` and `s_y` the sums of the scaled records, added in order, the value
  is `Σ min(x_i/s_x, y_i/s_y)`, added in order, held at 1 from above.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares and their smaller parts with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums.
