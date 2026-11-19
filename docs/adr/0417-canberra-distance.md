# ADR 0417: The Canberra distance

Status: accepted, 2026-11-19.

## Context

The Canberra distance is an `L1` distance in which each coordinate's difference is scaled
by the coordinates' own size, so small coordinates count as much as large ones. It is used
to compare spectra and feature vectors whose entries span several orders of magnitude.
Unlike the distribution measures (ADRs 0407–0416) it takes plain vectors, of any sign, and
does not normalize them.

## Decision

- **The API.**
  - Python: `canberra_distance(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.CanberraDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The value.**
  - `d(x, y) = Σᵢ |xᵢ − yᵢ|/(|xᵢ| + |yᵢ|)`.
  - Indices where both are zero are dropped (the term is `0/0` and is taken as 0). Per
    index, the difference's magnitude over the sum of magnitudes; the terms are summed in
    order.
  - Symmetric, a metric, from 0 to the length.
- **The rules.**
  - `x` and `y` are real and finite, of equal length at least 1.

## Consequences

- The cost is one pass.
- A term can lose all its accuracy to overflow when `|xᵢ| + |yᵢ|` passes the largest
  double; the inputs are taken to be well inside that range.
- **Vectors.**
  - The generator forms the distance exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
