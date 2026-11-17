# ADR 0209: LSF to prediction filter

Status: accepted, 2026-11-17. It is the inverse of ADR 0208.

## Context

A coder that quantizes or interpolates line spectral frequencies must turn them back into a
prediction-error filter for synthesis.

## Decision

- **The API.**
  - Python: `lsf_to_lpc(frequencies)` in `dsp`.
  - C#: `Dsp.LsfToLpc`.
  - Both return the real filter `a`, with `a_0 = 1` and `p + 1` taps, for `p` frequencies.
- **The factors.**
  - The ascending frequencies alternate between the polynomials, starting with `P`:
    `ω_0, ω_2, …` go to `P` and `ω_1, ω_3, …` to `Q`. This matches ADR 0208, where the lowest
    root is `P`'s.
  - Each frequency contributes the factor `1 − 2 cos ω·z^−1 + z^−2`.
  - The trivial factors are:
    - for even `p`: `1 + z^−1` in `P` and `1 − z^−1` in `Q`;
    - for odd `p`: `1 − z^−2` in `Q`, and none in `P`.
  - The products are formed in ascending frequency order.
- **The filter.** It is `a = (P + Q)/2`, without its last tap. That tap is zero in exact
  arithmetic.
- **The rules.** The frequencies must be real, finite, at least one, strictly ascending and
  inside `(0, π)`.

## Consequences

- **Vectors.**
  - Filters are expanded from chosen roots, and their LSFs come from ADR 0208's closed forms
    for orders 1 to 3. The expected filter is that original expansion.
  - An order-4 case multiplies the factors out with the stdlib.
