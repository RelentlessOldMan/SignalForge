# ADR 0233: Savitzky–Golay smoothing and derivatives

Status: accepted, 2026-11-17.

## Context

A Savitzky–Golay filter fits a polynomial by least squares to each window of samples. It then
evaluates the polynomial, or one of its derivatives, at the window's centre. It smooths while
keeping peak heights and widths better than a moving average, and gives smoothed derivatives.

## Decision

- **The API.**
  - Python: `savgol_coefficients(length, order, *, derivative=0, position=0)` and
    `savgol_filter(samples, length, order, *, derivative=0)` in `dsp`.
  - C#: `Dsp.SavgolCoefficients` and `Dsp.SavgolFilter`, for real samples.
- **The coefficients.**
  - With `h = (length − 1)/2`, the window offsets are `k = −h … h`. The coefficients are
    indexed `0 … length − 1` in increasing `k`.
  - `c[k + h]` are the weights for which `Σ_k c[k + h]·x[k]` is the `derivative`-th derivative,
    with respect to the sample index, of the degree-`order` least-squares polynomial through
    `(k, x[k])`. The derivative is evaluated at offset `position`.
  - They are applied as a correlation, not a convolution: `y = Σ_k c[k + h]·x[n + k]`.
- **The computation.**
  - The offsets are scaled to `t = k/s`, with `s = max(h, 1)`.
  - The Vandermonde matrix `A[k, i] = t^i`, for `i = 0 … order`, is factored as `QR` by
    modified Gram–Schmidt.
  - `v[i] = i!/(i−d)!·(position/s)^(i−d)/s^d` for `i ≥ d`, and 0 for `i < d`.
  - Solving `Rᵀz = v` by forward substitution gives `c = Qz`.
- **The filter.**
  - The samples must be at least `length` long.
  - For `h ≤ n < L − h`, `y[n] = Σ_k c₀[k + h]·x[n + k]`, using the centre coefficients.
  - Each edge uses the polynomial fitted to the first or the last `length` samples, evaluated at
    the sample's own offset in that window. For `n < h`, that is
    `y[n] = Σ_j c_{n−h}[j]·x[j]`. For `n ≥ L − h`, it is `y[n] = Σ_j c_{n−(L−1−h)}[j]·x[L − length + j]`.
  - So a polynomial of degree `≤ order` is reproduced exactly, edges included, up to round-off.
- **The rules.**
  - `length` must be an odd integer `≥ 1`.
  - `order` must be an integer with `0 ≤ order < length`.
  - `derivative` must be an integer with `0 ≤ derivative ≤ order`.
  - `position` must be an integer with `|position| ≤ h`.
  - The samples must be real and finite, and at least `length` long.

## Consequences

- **Vectors.** The generator solves the normal equations in exact rational arithmetic, with
  unscaled offsets. It checks the classic Savitzky–Golay table entries:
  - `(−3, 12, 17, 12, −3)/35` for length 5, order 2;
  - `(−2, −1, 0, 1, 2)/10` for its first derivative.
