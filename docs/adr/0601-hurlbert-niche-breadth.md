# ADR 0601: Hurlbert's niche breadth

Status: accepted, 2026-11-23.

## Context

Hurlbert (1978) measured the breadth of a consumer's use against what is available to it:
with the shares of use `p_i = x_i/Σx` and of availability `r_i = a_i/Σa`,
`B' = 1/Σ p_i²/r_i`. It is 1 when the consumer uses each kind in proportion to its
availability, and its least, `r_min`, the smallest availability share, when it uses only the
scarcest kind. The standardized form `B'_A = (B' − r_min)/(1 − r_min)` runs from 0 to 1.

## Decision

- **The API.**
  - Python: `hurlbert_niche_breadth(x, available, *, standardized=False)` in
    `measurements`, giving a float.
  - C#: `Measurements.HurlbertNicheBreadth(ReadOnlySpan<double> x,
    ReadOnlySpan<double> available, bool standardized = false)`.
- **The form.** Each record is first divided by its largest value, then by its sum, added
  in order, to give the shares. The sum `Σ (p_i p_i)/r_i` is added in order; `B'` is its
  reciprocal, held at 1 from above. `r_min` is the smallest availability share. The
  standardized form is held to 0 to 1.
- **The rules.**
  - The records as for `hurlbert_overlap`: one-dimensional, real, finite, at least 0, not
    empty, with a value above 0, the same length; `available` above 0 everywhere.
  - An availability share that underflows to 0, and a sum that overflows, are refused.
  - The standardized form needs at least two kinds, since with one `r_min = 1`.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares and both forms with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums.
