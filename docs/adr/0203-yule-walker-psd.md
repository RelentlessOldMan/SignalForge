# ADR 0203: Yule-Walker AR PSD

Status: accepted, 2026-11-17. It is the first parametric spectral estimator. It builds on the
autocorrelation (ADR 0148) and Levinson-Durbin (ADR 0149).

## Context

Welch and multitaper are nonparametric. An autoregressive model gives a smooth spectrum with
sharp peaks from a short record. Yule-Walker fits one from the biased autocorrelation, and that
fit is always stable.

## Decision

- **The API.**
  - Python: `yule_walker_psd(samples, sample_rate, order, *, nfft=None, one_sided=None)` in
    `spectral`.
  - C#: `Spectral.YuleWalkerPsd`. The real overload takes `oneSided = true`; the `Complex`
    overload is two-sided. This follows the multitaper PSD.
  - Both return a `SpectralDensity`.
- **The model.**
  - `r` is the biased autocorrelation, lags `0 … p`, with no mean removed.
  - Levinson-Durbin gives `a` (`a[0] = 1`) and the prediction error `σ²`.
- **The density.**
  - At FFT bin `k` of `M = nfft`, the two-sided density is `σ² / (fs·|A_k|²)`, where
    `A_k = Σ_j a_j e^(−2πi jk/M)`.
  - It is then folded as Welch does: one-sided bins `0 … ⌊M/2⌋` with the interior doubled, or
    all bins shifted.
  - In this scaling, `Σ psd · fs/M` tends to `r[0]` as `M` grows, which is the record's mean
    power.
- **The fields.**
  - `nperseg = N` and `num_segments = 1`.
  - `bin_width = fs/M`.
  - `enbw_hz = fs/N`: a model has no window, so the record's rectangular resolution is
    reported.
- **The rules.**
  - The samples are one-dimensional and finite, and not all zero.
  - `sample_rate` is positive and finite.
  - `1 ≤ order < N`, an integer.
  - `nfft ≥ order + 1`; it defaults to `N`.
  - A one-sided result needs real samples.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors.** Their expected values solve the Yule-Walker normal equations directly: Cramer's
  rule for orders 1 and 2, real and complex. `|A|²` is evaluated with `cmath` at each bin, not
  by Levinson's recursion or an FFT.
- **Later work.** Burg's method and the covariance methods would reuse this result shape.
