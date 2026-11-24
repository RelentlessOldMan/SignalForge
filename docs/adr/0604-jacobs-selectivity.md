# ADR 0604: Jacobs' selectivity index

Status: accepted, 2026-11-23.

## Context

Jacobs (1974) changed Ivlev's electivity so that it does not depend on how abundant a kind
is: with the share of use `p_i = x_i/Σx` and of availability `r_i = a_i/Σa`,
`D_i = (p_i − r_i)/(p_i + r_i − 2 p_i r_i)`. It is the log odds ratio of use to availability
mapped onto −1 to 1: −1 for a kind available but not used, 0 for a kind used as it is
available, 1 for the only kind used.

## Decision

- **The API.**
  - Python: `jacobs_selectivity(x, available)` in `measurements`, giving an array of
    floats.
  - C#: `Measurements.JacobsSelectivity(ReadOnlySpan<double> x,
    ReadOnlySpan<double> available)`, giving `double[]`.
- **The form.** Each record is first divided by its largest value, then by its sum, added
  in order, to give the shares. The denominator is written `p_i (1 − r_i) + r_i (1 − p_i)`,
  the same value without the cancellation of `p + r − 2pr`. Each value is held to −1 to 1.
- **Equal shares.** A kind with `p_i = r_i` is 0. This also defines the one case where the
  denominator is 0, `p_i = r_i = 1`: a single kind, used as it is available.
- **The rules.**
  - The records as for `ivlev_electivity`: one-dimensional, real, finite, at least 0, not
    empty, with a value above 0, the same length; `available` above 0 everywhere.
  - An availability share that underflows to 0 is refused, as for `ivlev_electivity`.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares and the values with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the shares.
