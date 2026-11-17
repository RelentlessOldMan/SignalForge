# ADR 0207: LPC cepstrum

Status: accepted, 2026-11-17. It works from the output of `levinson` or `burg` (ADR 0149,
ADR 0205).

## Context

Speech and audio features often use the cepstrum of the all-pole model rather than the
cepstrum of the raw spectrum. The model's cepstrum is smooth, and it follows from the
prediction coefficients by a short recursion, without any FFT.

## Decision

- **The API.**
  - Python: `lpc_cepstrum(coefficients, error, num_coefficients)` in `dsp`.
  - C#: `Dsp.LpcCepstrum`, with real and complex overloads.
  - Both return `c_0 … c_{num_coefficients−1}`.
- **The definition.** `c_n` are the coefficients of the power series `ln(σ/A(z)) = Σ c_n z^−n`,
  where `A(z) = Σ_j a_j z^−j` and `a_0 = 1`:
  - `c_0 = ln σ = ½ ln error`;
  - `c_n = −a_n − (1/n) Σ_{k=1}^{n−1} k·c_k·a_{n−k}`, with `a_j = 0` for `j > p`.
  - When `A` is minimum phase, which `levinson` and `burg` guarantee, this is the complex
    cepstrum of the model `σ/A`. The log-spectrum of `σ²/|A|²` is then `2 Re Σ c_n e^−iωn`.
  - The recursion is not checked for minimum phase. It is a formal series.
- **The output type.** Real coefficients give a real array, and complex coefficients give a
  complex array.
- **The rules.**
  - The coefficients must be finite, at least one, with `a_0 = 1` exactly.
  - `error` must be positive and finite.
  - `num_coefficients ≥ 1`.

## Consequences

- **Vectors.** With `A = Π (1 − r_i z^−1)`, `−ln A = Σ_n (Σ_i r_iⁿ)/n · z^−n`, so:
  - order 1 gives `c_n = (−a_1)ⁿ/n`;
  - order 2 gives `c_n = (r_1ⁿ + r_2ⁿ)/n` from its chosen roots, real, complex-conjugate and
    complex.
