# ADR 0600: Hurlbert's niche overlap

Status: accepted, 2026-11-23.

## Context

Hurlbert (1978) measured the overlap of two consumers against what is available to them:
with the shares of use `p_i = x_i/Σx`, `q_i = y_i/Σy` and the shares of availability
`r_i = a_i/Σa`, `L = Σ p_i q_i/r_i`. It is the density of encounters between the two,
relative to what it would be if both used each kind in proportion to its availability, when
`L = 1`. It is 0 when they share no kind, and above 1 when both crowd onto the same scarce
kinds. It has no upper bound.

The name is `available` rather than `a`: `a` is the count of shared kinds in the presence
measures.

## Decision

- **The API.**
  - Python: `hurlbert_overlap(x, y, available)` in `measurements`, giving a float.
  - C#: `Measurements.HurlbertOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y,
    ReadOnlySpan<double> available)`.
- **The form.** Each record is first divided by its largest value, then by its sum, added
  in order, to give the shares. The value is `Σ (p_i q_i)/r_i`, added in order.
- **The rules.**
  - Each record as for `pianka_overlap`: one-dimensional, real, finite, at least 0, not
    empty, with a value above 0; all three the same length.
  - `available` above 0 everywhere, since a kind that is not available cannot be used.
  - An availability share that underflows to 0, so that the ratio is not defined, and a sum
    that overflows, are refused rather than returned as infinite.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares and the sum with fractions.
  - The error cases include an availability share that underflows and a sum that overflows.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums.
