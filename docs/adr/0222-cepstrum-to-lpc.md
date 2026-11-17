# ADR 0222: Cepstrum to prediction filter

Status: accepted, 2026-11-17. It inverts ADR 0207's LPC cepstrum.

## Context

Cepstral features are often smoothed, averaged or quantized, and then turned back into an
all-pole model for synthesis or for a spectral envelope. ADR 0207's recursion can be solved for
`a_n` instead of `c_n`.

## Decision

- **The API.**
  - Python: `cepstrum_to_lpc(cepstrum, order)` in `dsp`.
  - C#: `Dsp.CepstrumToLpc`, with real and complex overloads.
  - Both return the prediction-error filter `a_0 … a_order`, with `a_0 = 1`. The output has the
    type of the input.
- **The value.**
  - `a_n = −c_n − (1/n) Σ_{k=1}^{n−1} k·c_k·a_{n−k}` for `n = 1 … order`. This is ADR 0207's
    recursion solved for `a_n`. It is the series of `exp(−Σ_{n≥1} c_n z^−n)`, truncated after
    `z^−order`.
  - `c_0` is not used. The model's prediction error is `exp(2c_0)`, and the caller can take it
    from there.
  - If `c` came from an order-`p` model and `order = p`, the result is that model exactly. A
    smaller `order` gives the truncated series, and that need not be the best fit of that order.
  - Minimum phase is not checked, as in ADR 0207.
- **The rules.**
  - The cepstrum must be finite and have at least `order + 1` values.
  - `order` must be an integer `≥ 1`.

## Consequences

- **Vectors.** They use ADR 0207's closed forms in exact fractions.
  - From roots `r_i`, `c_n = (Σ_i r_iⁿ)/n`, and `a` is the coefficients of `Π(1 − r_i z^−1)`.
  - The cases cover order 1, two real roots, a complex pair, and complex roots.
  - One case truncates an order-2 cepstrum to order 1, where `a_1 = −c_1`.
