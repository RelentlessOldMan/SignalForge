# ADR 0602: Manly's alpha

Status: accepted, 2026-11-23.

## Context

Manly, Miller and Cook (1972), and Chesson (1978), measured a consumer's preference for each
kind of resource by its use relative to its availability: with the shares of use
`p_i = x_i/Σx` and of availability `r_i = a_i/Σa`, `α_i = (p_i/r_i)/Σ_j (p_j/r_j)`. The
values sum to 1; each is `1/n`, for `n` kinds, when the consumer uses the kinds as they are
available, above `1/n` for a kind it prefers and below for one it avoids.

## Decision

- **The API.**
  - Python: `manly_alpha(x, available)` in `measurements`, giving an array of floats.
  - C#: `Measurements.ManlyAlpha(ReadOnlySpan<double> x, ReadOnlySpan<double> available)`,
    giving `double[]`.
- **The form.** Each record is first divided by its largest value, then by its sum, added
  in order, to give the shares. The ratios `w_i = p_i/r_i` are added in order; each `α_i` is
  `w_i/Σw`, held at 1 from above. The ratios are taken on the shares rather than on the raw
  values so that a sum of raw values cannot overflow.
- **The rules.**
  - The records as for `hurlbert_niche_breadth`: one-dimensional, real, finite, at least 0,
    not empty, with a value above 0, the same length; `available` above 0 everywhere.
  - An availability share that underflows to 0, and a sum of ratios that overflows, are
    refused.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares and the values with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums.
