# ADR 0347: Slope entropy

Status: accepted, 2026-11-18.

## Context

Slope entropy (Cuesta-Frau, 2019) sits between permutation entropy (ADR 0325), which keeps
only order, and increment entropy (ADR 0344). Each step inside a window becomes one of five
symbols, by how steep it is against two fixed thresholds. Because the thresholds are in the
signal's own units, the measure is not scale-invariant, by design.

## Decision

- **The API.**
  - Python: `slope_entropy(samples, m, gamma=1.0, delta=1e-3)` in `measurements`, giving a
    float.
  - C#: `Measurements.SlopeEntropy(ReadOnlySpan<double> samples, int m, double gamma = 1,
    double delta = 1e-3)`.
- **The value.**
  - Each of the `N − m + 1` windows of `m` consecutive samples has `m − 1` steps
    `d = x_{i+1} − x_i`.
  - Each step becomes a symbol, as in Cuesta-Frau's paper:
    - `+2` if `d > γ`,
    - `+1` if `δ < d ≤ γ`,
    - `0` if `|d| ≤ δ`,
    - `−1` if `−γ ≤ d < −δ`,
    - `−2` if `d < −γ`.
  - The value is the Shannon entropy in nats, `−Σ p·ln p`, of the symbol patterns over the
    windows. It is not normalized.
- **The rules.**
  - `samples` real, one-dimensional and finite, at least `m` of them.
  - `m` an integer from 2 to 16.
  - `γ` and `δ` finite with `0 ≤ δ < γ`.

## Consequences

- **Vectors.**
  - The samples are dyadic, so every step is exact in float. The generator classifies the
    steps in rationals against the exact thresholds and counts exactly. The logarithms are
    taken in float.
  - The cases include steps exactly on `γ` and on `δ`.
  - The tolerance is `abs 1e-14, rel 1e-13`.
