# ADR 0226: Farrow variable delay

Status: accepted, 2026-11-17. It builds on ADR 0040 (fractional delay) and ADR 0225 (the
Lagrange FIR).

## Context

ADR 0040 delays a whole signal by one fixed amount, and said a Farrow structure for
time-varying delays could come later. Delays that change from sample to sample are common:
Doppler, a moving path, timing recovery and asynchronous rate conversion. The Farrow structure
writes each Lagrange tap as a polynomial in the fractional part `μ`. The sub-filters are then
fixed, and only the Horner evaluation in `μ` changes per sample.

## Decision

- **The API.**
  - Python: `farrow_delay(samples, delays, *, order=3)` in `channel`, beside `fractional_delay`.
  - C#: `Channel.FarrowDelay(samples, delays, order = 3)`.
  - The output is complex and as long as the input, like `fractional_delay`.
- **The value.** Let `N = order`, `n = 0 … L−1`, and `x[m] = 0` outside `0 … L−1`.
  - The read position is `p = n − delays[n]`.
  - Let `q = p − (N−1)/2`, `b = ⌊q⌋` and `μ = q − b`, so `μ ∈ [0, 1)`.
  - Then `y[n] = Σ_{j=0}^{N} L_j(μ + (N−1)/2)·x[b+j]`, with the Lagrange basis
    `L_j(u) = Π_{m≠j} (u − m)/(j − m)`.
  - This is the order-`N` Lagrange interpolator through the `N + 1` samples nearest `p`. It reads
    at offset `u = μ + (N−1)/2` from `b`, which is ADR 0225's best range.
  - It equals `lagrange_fir(N − u, N)` applied at sample `b + N`.
- **The Farrow form.**
  - Each `L_j(μ + (N−1)/2)` is expanded once as a polynomial `Σ_k c[j][k] μ^k`. It is built as a
    product over increasing `m ≠ j`, multiplying by `(μ + (N−1)/2 − m)/(j − m)` at each step.
  - Per sample, the sub-filter outputs are `v_k = Σ_j c[j][k]·x[b+j]`, summed over increasing `j`.
  - `y` is then `v` evaluated at `μ` by Horner's rule, from `v_N` down to `v_0`.
  - The polynomial is in `μ ∈ [0, 1)`, not `u`, which keeps it well conditioned for moderate
    orders.
- **Integer delays.** For odd `N`, an integer delay gives `μ = 0`. The constant terms are exact,
  so the result is an exact shift. For even `N`, an integer delay gives `μ = 1/2` and an
  interpolated value, though one exact for polynomials.
- **The rules.**
  - `delays` must have the same length as `samples`, and every delay must be finite. A negative
    delay advances.
  - `order` must be an integer `≥ 1`.
  - Empty input gives empty output.

## Consequences

- **Vectors.**
  - The expected values come from exact rational arithmetic in the generator. It uses the
    Lagrange product directly, not the Farrow expansion.
  - The delays are binary fractions, so `p`, `b` and `μ` are exact.
  - The generator checks that every interior output of a polynomial input of degree `≤ N` is
    the polynomial's value at `p`.
- **Accuracy.** The monomial Farrow form loses accuracy as the order grows. Orders up to about 7
  are the intended use.
