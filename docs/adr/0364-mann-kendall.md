# ADR 0364: Mann–Kendall trend test

Status: accepted, 2026-11-18.

## Context

The Mann–Kendall test (Mann 1945, Kendall 1975) is the standard distribution-free test for a
monotone trend. It is used throughout hydrology and climate work. It counts the pairs that
rise, minus the pairs that fall.

## Decision

- **The API.**
  - Python: `mann_kendall(samples)` in `measurements`, giving a frozen dataclass
    `MannKendall(s, z)`.
  - C#: `Measurements.MannKendall(ReadOnlySpan<double> samples)`, giving the record
    `MannKendall(long S, double Z)`.
- **The value.**
  - `S = Σ_{i<j} sign(x_j − x_i)`.
  - The variance is `σ² = (N(N − 1)(2N + 5) − Σ_g t_g(t_g − 1)(2t_g + 5))/18`, where `t_g`
    are the sizes of the groups of equal samples.
  - `z = (S − 1)/σ` if `S > 0`, `(S + 1)/σ` if `S < 0`, and 0 if `S = 0`. This is the usual
    continuity correction.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `N ≥ 2`, and not every sample equal, so `σ² > 0`.

## Consequences

- **Vectors.**
  - `S` and `σ²` are integers, computed exactly.
  - The square root and the quotient are taken in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
