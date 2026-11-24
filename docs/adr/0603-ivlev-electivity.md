# ADR 0603: Ivlev's electivity

Status: accepted, 2026-11-23.

## Context

Ivlev (1961) measured a consumer's selection of each kind of resource by comparing its share
of use `p_i = x_i/Σx` with its share of availability `r_i = a_i/Σa`:
`E_i = (p_i − r_i)/(p_i + r_i)`. It is −1 for a kind that is available but not used, 0 for a
kind used as it is available, and approaches 1 for a kind used far more than it is
available.

## Decision

- **The API.**
  - Python: `ivlev_electivity(x, available)` in `measurements`, giving an array of floats.
  - C#: `Measurements.IvlevElectivity(ReadOnlySpan<double> x,
    ReadOnlySpan<double> available)`, giving `double[]`.
- **The form.** Each record is first divided by its largest value, then by its sum, added
  in order, to give the shares. Each value is `(p_i − r_i)/(p_i + r_i)`, held to −1 to 1.
  The shares are at most 1, so nothing can overflow.
- **The rules.**
  - The records as for `manly_alpha`: one-dimensional, real, finite, at least 0, not empty,
    with a value above 0, the same length; `available` above 0 everywhere.
  - An availability share that underflows to 0 is refused, as for `manly_alpha`: it would
    give 0/0 for a kind that is not used.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares and the values with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the shares.
