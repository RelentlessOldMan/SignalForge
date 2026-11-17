# ADR 0217: Itakura-Saito distance between AR models

Status: accepted, 2026-11-17. It uses the model autocorrelation of ADR 0214.

## Context

Speech recognition and coder evaluation compare two all-pole models by the Itakura-Saito
distance between their spectra. For AR models this has a closed form, so no spectrum has to be
sampled.

## Decision

- **The API.**
  - Python: `itakura_saito(reference, reference_error, test, test_error)` in `dsp`, returning a
    `float`.
  - C#: `Dsp.ItakuraSaito`, with real and complex overloads, returning `double`.
- **The arguments.**
  - `reference` and `test` are prediction-error filters with `a[0] = 1`, of any orders `≥ 0`.
  - `reference_error` and `test_error` are their prediction errors `σ²`.
  - The model spectra are `S = σ²/|A(e^{jω})|²`.
- **The value.** It is `d = mean_ω (S_r/S_t − ln(S_r/S_t) − 1)`, which has the closed form
  `d = q/σ_t² − ln(σ_r²/σ_t²) − 1`:
  - `q = Σ_{i,j} a_t[i]·conj a_t[j]·r_r[j − i]` is the power of the reference process after the
    test filter;
  - `r_r` is the reference model's autocorrelation (ADR 0214), with `r[−m] = conj r[m]`;
  - `r_r[0] = σ_r²/Π(1 − |k|²)`, with `k` from `lpc_to_reflection`. For order 0, `r_r = [σ_r², 0, …]`;
  - the log term holds because both filters are minimum phase, so `mean ln |A|² = 0`.
  - `d ≥ 0`, it is 0 only for equal models, and it is not symmetric.
- **The rules.**
  - Both filters must be finite and non-empty, with `a[0] = 1`.
  - Both must be minimum phase: every recovered `|k| < 1`.
  - Both errors must be positive and finite.

## Consequences

- **Vectors.**
  - Real cases are evaluated exactly in fractions, apart from the logarithm.
  - Every case is cross-checked in the generator by a stdlib numerical integral of
    `S_r/S_t − ln(S_r/S_t) − 1` over a 4096-point grid.
  - The integral does not depend on any autocorrelation sign convention, so it pins the
    complex case too.
