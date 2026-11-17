# ADR 0206: AR order selection

Status: accepted, 2026-11-17. It builds on the Burg AR fit (ADR 0205).

## Context

An AR estimate needs an order. If the order is too low, peaks merge. If it is too high, the
estimate shows spurious peaks. Akaike's final prediction error and his information criterion
are the standard objective choices. Each needs only the prediction error at every order up to
a limit, and Burg's recursion produces those errors for free.

## Decision

- **The API.**
  - Python: `ar_order_selection(samples, max_order)` in `dsp`, returning
    `ArOrderSelection(errors, fpe, aic, fpe_order, aic_order)`.
  - C#: `Dsp.ArOrderSelection`, with real and complex overloads.
- **The errors.** `errors[p]` for `p = 0 … P`:
  - `σ²_0 = mean |x|²`;
  - `σ²_p = σ²_{p−1}·(1 − |k_p|²)`, with the Burg reflection coefficients `k_p`.
  - The mean is not removed.
- **The criteria.** With `N` samples:
  - `FPE_p = σ²_p·(N + p + 1)/(N − p − 1)`;
  - `AIC_p = N·ln σ²_p + 2p`.
  - `fpe_order` and `aic_order` are the orders that minimize each criterion. A tie goes to the
    lowest order.
- **The rules.**
  - `1 ≤ max_order ≤ N − 2`, so the FPE denominator stays positive.
  - The samples must be finite.
  - Burg's own rules apply: a predictable record is `invalid_argument`.

## Consequences

- **Vectors.**
  - `x = [1, 2, 3]` is exact, from ADR 0205's `k₁ = −8/9`.
  - An impulse `[1, 0, 0, 0, 0, 0]` has every `k = 0`. Its errors stay at `1/6`, so both
    criteria choose order 0.
  - The rest come from the stdlib error recursion.
