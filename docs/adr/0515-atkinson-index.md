# ADR 0515: The Atkinson index

Status: accepted, 2026-11-20.

## Context

The Atkinson index measures inequality as the share of the total that could be given up,
if the rest were shared equally, for the same social welfare. Its parameter, the
inequality aversion `ε ≥ 0`, sets how much weight falls on the lowest values: at `ε = 0`
the index is 0 for every record, and as `ε` grows it tends to `1 − min/μ`.

## Decision

- **The API.**
  - Python: `atkinson_index(samples, epsilon)` in `measurements`, giving a float.
  - C#: `Measurements.AtkinsonIndex(ReadOnlySpan<double> samples, double epsilon)`.
- **The value.**
  - With `rᵢ = xᵢ/μ`, `μ` the mean: `A = 1 − ((1/n)·Σ rᵢ^(1−ε))^(1/(1−ε))` for `ε ≠ 1`,
    and `A = 1 − exp((1/n)·Σ ln rᵢ)` at `ε = 1`, the geometric mean over the mean; so
    `A = 1 − exp(−L)` there, `L` the mean log deviation (ADR 0514). At `ε = 2` it is one
    less the harmonic mean over the mean.
  - From 0, when every value is equal, to below 1. Unchanged when every value is scaled
    by the same positive factor; it does not fall as `ε` grows.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value greater than
    0, as for the mean log deviation: some texts allow a 0 when `ε < 1`; this one does not.
  - `ε` finite and at least 0.

## Consequences

- The cost is two passes and a power per value.
- **Vectors.**
  - The generator takes each ratio to the mean exactly in rationals, and each power as
    `exp(p·ln r)` in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-13`: the outer power can magnify the error of the
    inner mean.
