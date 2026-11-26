# ADR 0618: Hopkins' statistic

Status: accepted, 2026-11-23.

## Context

Hopkins and Skellam (1954) compared two kinds of distance in a pattern of individuals in a
plane: `u`, from a point placed at random to the nearest individual, and `w`, from an
individual chosen at random to its nearest neighbour. When the individuals are placed at
random the two have the same distribution; when they are clumped the points fall in empty
space and the `u` are longer. Hopkins' statistic is `H = Σu²/(Σu² + Σw²)`, the squared
distances being what is distributed as χ² at random. It is about 1/2 at random, near 1 for
a clumped pattern and near 0 for a regular one.

## Decision

- **The API.**
  - Python: `hopkins_statistic(point_distances, individual_distances)` in `measurements`,
    giving a float.
  - C#: `Measurements.HopkinsStatistic(ReadOnlySpan<double> pointDistances,
    ReadOnlySpan<double> individualDistances)`.
- **The form.** With `t` the largest distance in either sample, `a = Σ(u/t)²` and
  `b = Σ(w/t)²` added in order, the value is `a/(a + b)`, held to [0, 1]. Scaling by `t`
  keeps the squares from overflowing. The samples are taken as given and need not be the
  same size; the usual design takes the same number of each, which is what makes `H` about
  1/2 at random.
- **The rules.**
  - Each sample one-dimensional, real, finite, at least 0, not empty, with a value above 0.
  - **Why each sample needs a value above 0 (review, 2026-11-26).** With one sample all 0
    the value is 0 or 1 whatever the other sample holds. That says nothing about the pattern,
    and in practice means a sample was lost or the two were swapped. With both all 0 it is
    0/0. A pattern where one sample really is all 0 (individuals stacked on the same spots)
    gives the same answer either way, so refusing it loses nothing.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the value with fractions.
  - The tolerance is `abs 1e-15, rel 1e-14`, for the rounding of the two sums.
