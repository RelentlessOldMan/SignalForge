# ADR 0607: Strauss' linear selection index

Status: accepted, 2026-11-23.

## Context

Strauss (1979) measured a consumer's selection of each kind of resource by the difference of
its share of use `p_i = x_i/Σx` and its share of availability `r_i = a_i/Σa`:
`L_i = p_i − r_i`. It is 0 for a kind used as it is available, negative for one avoided and
positive for one preferred, from −1 to 1. Unlike the ratio indices it does not divide by
the availability.

## Decision

- **The API.**
  - Python: `strauss_selection(x, available)` in `measurements`, giving an array of floats.
  - C#: `Measurements.StraussSelection(ReadOnlySpan<double> x,
    ReadOnlySpan<double> available)`, giving `double[]`.
- **The form.** Each record is first divided by its largest value, then by its sum, added
  in order, to give the shares. Each value is `p_i − r_i`. Both shares are from 0 to 1, so
  the difference is from −1 to 1 without holding.
- **The rules.**
  - The records as for `savage_selection_ratio`: one-dimensional, real, finite, at least 0,
    not empty, with a value above 0, the same length; `available` above 0 everywhere.
  - An availability share that underflows to 0 is not refused, as it is for the ratio
    indices: nothing divides by it, and the difference is still the value to double
    precision.
  - **Why `available` must be above 0 everywhere (review, 2026-11-26).** A kind with no
    availability cannot be chosen, so use above 0 there means the two records disagree.
    Where use is 0 too, `p − r = 0` is defined, but the kind carries no information. The
    rule matches the ratio indices (ADRs 0602–0606 and 0608), so a pair of records accepted by one
    selection index is accepted by all of them. A caller drops such kinds before the call.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares and the differences with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the shares.
