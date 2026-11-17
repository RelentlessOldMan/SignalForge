# ADR 0227: Thiran allpass fractional delay

Status: accepted, 2026-11-17. It sits beside ADR 0225 (the Lagrange FIR).

## Context

A Lagrange FIR (ADR 0225) delays with a flat magnitude only near DC. An allpass filter has unit
magnitude at every frequency, and Thiran's design (1971) makes its group delay maximally flat at
DC. The coefficients have a closed form. These filters are the usual fractional delay in
waveguide synthesis and in delay lines where the magnitude must stay exactly 1.

## Decision

- **The API.** Python: `thiran_allpass(delay, order)` in `dsp`. C#: `Dsp.ThiranAllpass(delay, order)`.
  - Both return the `order + 1` denominator coefficients `a`, with `a[0] = 1`.
  - The filter is `H(z) = z^(−N)·A(1/z)/A(z)`, so its numerator is `a` reversed:
    `y[n] = Σ_k a[N−k]·x[n−k] − Σ_{k≥1} a[k]·y[n−k]`.
- **The value.** With `N = order` and `D = delay`, `a_0 = 1` and, for `k = 1 … N`:
  - `a_k = (−1)^k·C(N, k)·Π_{n=0}^{N} (D − N + n)/(D − N + k + n)`.
  - It is computed as the sign times `C(N, k)`, built as `Π_{i=1}^{k} (N − k + i)/i`. That is then
    multiplied by the `N + 1` ratios in increasing `n`.
  - `a_0` is set to 1 directly. The product form also gives 1 there, but it is `0/0` at
    `D = N`.
  - The group delay at DC is exactly `D`, and it is maximally flat there. `D = N` gives
    `a = [1, 0, …, 0]`, the pure delay `z^(−N)`.
- **The rules.**
  - `delay` must be finite with `D > N − 1`. This keeps every denominator positive, and the filter
    is stable there (Thiran).
  - `order` must be an integer `≥ 1`.

## Consequences

- **Vectors.**
  - The expected values are exact fractions from the closed form.
  - Each case is checked against an independent identity. The DC group delay of
    `z^(−N)A(1/z)/A(z)` is `N − 2·Σ k a_k / Σ a_k`, which must equal `D`.
  - Order 1 is also checked against the textbook `a_1 = (1 − D)/(1 + D)`.
- **Direct form.** The result is a direct-form polynomial, not second-order sections. Factoring
  would need polynomial roots. For high orders, users should prefer a Lagrange or Farrow delay.
