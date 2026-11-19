# ADR 0366: Pettitt change-point test

Status: accepted, 2026-11-18.

## Context

Pettitt (1979) gave a rank-based test for one change in the level of a record at an unknown
time. For each split point it computes a Mann–Whitney statistic between the two parts. The
test statistic is the largest of these in absolute value, and its location is the estimated
change point.

## Decision

- **The API.**
  - Python: `pettitt(samples)` in `measurements`, giving a frozen dataclass
    `Pettitt(statistic, index, p_value)`.
  - C#: `Measurements.Pettitt(ReadOnlySpan<double> samples)`, giving the record
    `Pettitt(long Statistic, int Index, double PValue)`.
- **The value.**
  - For each split `t = 0 … N − 2`, `U_t = Σ_{i≤t<j} sign(x_j − x_i)`. It is positive when
    the later part is higher.
  - `statistic = K = max_t |U_t|`.
  - `index` is the smallest `t` with `|U_t| = K`. It is the last sample before the change.
  - `p_value = min(1, 2 exp(−6K²/(N³ + N²)))`, Pettitt's approximation.
  - The implementation uses the recurrence `U_t = U_{t−1} + Σ_k sign(x_k − x_t)`, starting
    from `U_{−1} = 0`.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `N ≥ 2`.
  - A constant record gives `K = 0`, `index = 0` and a p-value of 1.

## Consequences

- **Vectors.**
  - The generator takes every `U_t` by the double sum, not the recurrence, exactly in
    integers.
  - It forms the exponent `−6K²/(N³ + N²)` in rationals, then takes `exp` in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
