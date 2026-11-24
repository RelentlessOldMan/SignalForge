# ADR 0612: Morisita's index of dispersion

Status: accepted, 2026-11-23.

## Context

Morisita (1959) measured the dispersion of counts of individuals in `n` sampling units by
the chance that two individuals drawn without replacement are in the same unit, over that
chance if they were spread evenly at random:
`I_d = n Σ x_i (x_i − 1)/(Σx (Σx − 1))`. It is about 1 for counts drawn at random, below 1
for even counts, and `n` when every individual is in one unit. It does not depend on the
mean count.

`morisita_overlap` (ADR 0581) is his index of the overlap of two records, a different
measure.

## Decision

- **The API.**
  - Python: `morisita_dispersion(counts)` in `measurements`, giving a float.
  - C#: `Measurements.MorisitaDispersion(ReadOnlySpan<double> counts)`.
- **The form.** With `t` the largest count and the sums `s_1 = Σ x_i/t`,
  `s_2 = Σ(x_i/t)²` added in order, the value is `n (s_2 − s_1/t)/(s_1 (s_1 − 1/t))`: equal
  to the definition, and nothing in it can overflow. It is held to [0, n].
- **The rules.**
  - `counts` as for `green_index`: one-dimensional, real, finite, whole numbers at least 0,
    at least two units, a total above 1.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the value from the definition with fractions.
  - The tolerance is `abs 1e-14, rel 1e-13`, for the subtractions.
