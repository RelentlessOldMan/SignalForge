# ADR 0204: Burg AR PSD

Status: accepted, 2026-11-17. It is the second parametric estimator, with the result shape of
the Yule-Walker AR PSD (ADR 0203).

## Context

Yule-Walker's biased autocorrelation tapers the data implicitly. That blurs the peaks of short
records. Burg's method fits the reflection coefficients straight from the data, by minimizing
the forward and backward prediction errors together. It still guarantees `|k| ≤ 1`.

## Decision

- **The API.**
  - Python: `burg_psd(samples, sample_rate, order, *, nfft=None, one_sided=None)` in `spectral`.
  - C#: `Spectral.BurgPsd`, with a real overload (`oneSided = true`) and a `Complex` overload
    (two-sided).
  - Both return a `SpectralDensity`, with the fields of ADR 0203.
- **The recursion.**
  - It starts with `f = b = x`, `a = [1]` and `σ² = mean |x|²`.
  - At order `m = 1 … p`:
    - with `F = f[1:]` and `B = b[:-1]`, `k_m = −2 Σ F·B* / Σ (|F|² + |B|²)`;
    - then `f ← F + k_m·B` and `b ← B + k_m*·F`;
    - `a ← a + k_m·conj(reverse(a))`, which is Levinson's step;
    - `σ² ← σ²·(1 − |k_m|²)`.
  - The mean is not removed.
- **The density.** It is `σ²/(fs·|A_k|²)`, folded as in ADR 0203.
- **The rules.** These are ADR 0203's, plus two more:
  - a zero error energy at any order is `invalid_argument`;
  - so is `|k_m| ≥ 1`, which means the record is perfectly predictable and gives `σ² = 0`.

## Consequences

- **Vectors.** Their expected values come from a stdlib transcription of the error recursion,
  with `|A|²` evaluated with `cmath`.
  - The 3-sample real case `x = [1, 2, 3]` is checked against exact fractions:
    `k₁ = −8/9`, `k₂ = 77/85`, `a = [1, −144/85, 77/85]` and
    `σ² = (14/3)·(17/81)·(1296/7225)`.
  - Order 1 is checked against its closed form.
