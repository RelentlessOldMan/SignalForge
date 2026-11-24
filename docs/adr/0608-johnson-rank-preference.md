# ADR 0608: Johnson's rank preference index

Status: accepted, 2026-11-23.

## Context

Johnson (1980) measured a consumer's preference for each kind of resource by ranks rather
than shares, so that the result does not depend on which kinds are counted as available.
Each kind is ranked by its use, 1 for the most used, and by its availability, 1 for the most
available; the index for the kind is `t_i = rank of use − rank of availability`. A negative
value is a kind used more than its availability suggests: the more negative, the more
preferred. The values sum to 0.

## Decision

- **The API.**
  - Python: `johnson_rank_preference(x, available)` in `measurements`, giving an array of
    floats.
  - C#: `Measurements.JohnsonRankPreference(ReadOnlySpan<double> x,
    ReadOnlySpan<double> available)`, giving `double[]`.
- **The ranks.** From 1 for the largest; tied values all get the mean of the ranks they
  span, so the values are whole or half numbers and exact. The ranks are taken on the
  values as given: dividing by the largest value first could underflow and make two values
  tie.
- **The rules.**
  - The records as for `strauss_selection`: one-dimensional, real, finite, at least 0, not
    empty, with a value above 0, the same length; `available` above 0 everywhere.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator ranks each value by counting the values above it and the values equal
    to it, a different method from the sort both libraries use.
  - The values are exact, so the tolerance is 0.
