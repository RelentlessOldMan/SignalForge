# ADR 0218: Cepstral distance between AR models

Status: accepted, 2026-11-17. It uses the LPC cepstrum of ADR 0207.

## Context

The truncated cepstral distance is the usual cheap spectral distance between all-pole models.
It is close to the RMS log-spectral difference and needs no spectrum.

## Decision

- **The API.**
  - Python: `cepstral_distance(reference, test, num_coefficients)` in `dsp`, returning a `float`.
  - C#: `Dsp.CepstralDistance`, with real and complex overloads, returning `double`.
- **The value.** It is `d = sqrt(Σ_{n=1}^{L} |c_r[n] − c_t[n]|²)`, with `L = num_coefficients`.
  - The cepstra are those of `1/A` (ADR 0207, with `σ² = 1`).
  - `c_0` is left out, so the distance ignores gain, and the prediction errors are not
    arguments.
  - This is a change from the queued plan, which took two error arguments that the value
    never uses.
- **The rules.**
  - Both filters must be finite and non-empty, with `a[0] = 1`, of any orders `≥ 0`.
  - Both must be minimum phase, which the cepstrum recursion needs.
  - `num_coefficients` must be an integer `≥ 1`.

## Consequences

- **Vectors.** The expected values are closed forms from the poles. With
  `A = Π(1 − p_i z⁻¹)`, `c_n = Σ_i p_iⁿ/n`. Order 1 gives `c_n = (−a_1)ⁿ/n`. Real cases are exact
  fractions under the root, and complex poles are used too.
