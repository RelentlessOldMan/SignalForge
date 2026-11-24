# ADR 0606: Savage's selection ratio

Status: accepted, 2026-11-23.

## Context

Savage (1931) measured a consumer's selection of each kind of resource by the ratio of its
share of use `p_i = x_i/Σx` to its share of availability `r_i = a_i/Σa`: `w_i = p_i/r_i`,
the forage ratio. It is 0 for a kind not used, 1 for a kind used as it is available, and
above 1 for a kind preferred, with no upper bound but `1/r_i`. Savage's selection ratio (ADR 0606) is
these ratios divided by their sum.

## Decision

- **The API.**
  - Python: `savage_selection_ratio(x, available)` in `measurements`, giving an array of
    floats.
  - C#: `Measurements.SavageSelectionRatio(ReadOnlySpan<double> x,
    ReadOnlySpan<double> available)`, giving `double[]`.
- **The form.** Each record is first divided by its largest value, then by its sum, added
  in order, to give the shares. Each value is `p_i/r_i`, the same ratio as in
  `manly_alpha`.
- **The rules.**
  - The records as for `manly_alpha`: one-dimensional, real, finite, at least 0, not empty,
    with a value above 0, the same length; `available` above 0 everywhere.
  - An availability share that underflows to 0, and a ratio that overflows, are refused.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares and the ratios with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums.
