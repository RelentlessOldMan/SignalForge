# ADR 0208: Line spectral frequencies

Status: accepted, 2026-11-17. It works from the prediction-error filters of ADR 0149 and
ADR 0205.

## Context

Speech coders quantize and interpolate an all-pole model as line spectral frequencies (LSFs).
Their stability is easy to check, since minimum phase is the same as interlacing angles. They
also stay well behaved under small changes.

## Decision

- **The API.**
  - Python: `line_spectral_frequencies(coefficients)` in `dsp`.
  - C#: `Dsp.LineSpectralFrequencies`, for real coefficients only.
  - Both return `p` angles in radians per sample, in `(0, π)`, sorted ascending.
- **The polynomials.** With `a` padded by one zero to length `p + 2` and `r` its reverse:
  - `P = a + r`, which is symmetric;
  - `Q = a − r`, which is antisymmetric.
  - With the shifts `s_j = (p + 1)/2 − j`, they are real on the unit circle:
    - `F_P(ω) = Σ_j P_j cos(ω s_j)`;
    - `F_Q(ω) = Σ_j Q_j sin(ω s_j)`.
  - The trivial roots at `ω = 0` and `π` are excluded.
- **The root search.**
  - Each function is sampled at `ω_i = π i/G`, `i = 1 … G − 1`, with `G = 256(p + 1)`.
  - A change in the sign test `F > 0` between neighbours brackets a root.
  - The bracket is bisected on that same test until the midpoint equals an end, or for at
    most 200 halvings. The result is the bracket's midpoint.
  - The roots of both functions are pooled and sorted.
- **The rules.**
  - The coefficients must be finite and real, with `a_0 = 1` and order `p ≥ 1`.
  - Finding other than `p` roots is `invalid_argument`. It means the filter is not minimum
    phase, or an LSF lies within one grid step of `0` or `π`.

## Consequences

- **Vectors.** On the unit circle the polynomials factor into quadratics in `x = cos ω`, so
  orders 1 to 3 have closed forms:
  - order 1: `ω = arccos(−a₁)`;
  - order 2: `cos ω = (1 − a₁ − a₂)/2` and `cos ω = −(1 + a₁ − a₂)/2`;
  - order 3: the roots of `2x² + (a₁ + a₃)x + (a₂ − 1) = 0`, and `cos ω = (a₃ − a₁)/2`.
