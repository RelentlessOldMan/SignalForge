# ADR 0149: Linear prediction by Levinson-Durbin

Status: accepted, 2026-11-16. It builds on the autocorrelation (ADR 0148).

## Context

Linear prediction finds the filter `a` that best predicts each sample from the `p` before it.
The normal equations form a Hermitian Toeplitz system in the autocorrelation `r`.
Levinson-Durbin solves it in `O(p²)` and gives the reflection coefficients on the way.
Definitions differ on four points:

- the sign of `a`;
- whether `a[0] = 1` is included;
- where the conjugate goes for complex data;
- what happens when `r` is not positive definite.

## Decision

- **The API.**
  - Python: `levinson(r, order)`, returning `Levinson(coefficients, reflection, error)`.
  - C#: `Dsp.Levinson(r, order)`. It returns `Levinson(double[] Coefficients, double[]
    Reflection, double Error)` for real `r`, and `ComplexLevinson(Complex[] Coefficients,
    Complex[] Reflection, double Error)` for complex `r`.
- **The filter.** `a` is the prediction-error filter, with `a[0] = 1` and `order + 1` taps, in
  the form `e[n] = Σ_{j=0}^{p} a[j]·x[n−j]`. This is the `lfilter(a, 1, …)` form, so the
  predictor is `x̂[n] = −Σ_{j≥1} a[j] x[n−j]`.
  - It solves `Σ_j a[j]·r[i−j] = 0` for `i = 1 … p`, with `r[−k] = conj(r[k])` as in ADR 0148.
  - The error is `E = Σ_j a[j]·conj(r[j])`. It is real and positive.
- **The recursion.** Start from `E₀ = r[0]` and `a = [1]`. Then for `m = 1 … p`:
  - `acc = r[m] + Σ_{j=1}^{m−1} a[j]·r[m−j]`;
  - `k_m = −acc / E`;
  - `a[j] ← a[j] + k_m·conj(a[m−j])` for `j = 1 … m−1`, and `a[m] = k_m`;
  - `E ← E·(1 − |k_m|²)`.

  The `k_m` are the reflection coefficients, and they come back in order.
- **The rules.**
  - `r` is 1-D and finite, with at least `order + 1` lags. Extra lags are ignored.
  - `r[0]` is real and positive. A complex `r[0]` must have imaginary part 0.
  - `order` is an integer `≥ 1`. Python rejects floats and bools.
  - Every `|k_m| < 1`, which holds exactly when `r` up to lag `p` is positive definite.
    Otherwise the call is `invalid_argument`.

## Consequences

- **Biased lags.** The biased autocorrelation (ADR 0148) is always positive semidefinite. It
  fails only when the signal is exactly predictable, as a pure tone is.
- **Vectors.** These are solved by hand in Fractions. The generator checks each case by
  solving every order's normal equations with exact Gaussian elimination, which is independent
  of the recursion.
  - a first-order case.
  - an AR(1) sequence at order 2, whose `k₂` is 0.
  - a second-order case with both reflections nonzero.
  - extra lags.
  - two complex cases.
  - the errors.
- **Tests.**
  - The coefficients solve the Toeplitz system, compared with a dense solve.
  - Fitting a long simulated AR(2) process recovers its coefficients.
  - The error matches the mean square of the filtered residual.
