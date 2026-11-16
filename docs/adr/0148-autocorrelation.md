# ADR 0148: Autocorrelation

Status: accepted, 2026-11-16.

## Context

The autocorrelation compares a signal with delayed copies of itself. It shows periodicity and
feeds pitch estimators and linear prediction. Definitions differ on four points:

- which factor is conjugated;
- the scaling, which may be none, `1/N` or `1/(N − k)`;
- whether the mean is removed;
- which lags are returned.

## Decision

- **The API.**
  - Python: `autocorrelation(samples, max_lag=None, *, scaling="biased")`.
  - C#: `Dsp.Autocorrelation(samples, maxLag, scaling)` for real and complex spans, where
    `maxLag` is an `int?` and `scaling` is the enum `CorrelationScaling` (`Biased`, `Unbiased`,
    `None`).
- **The value.** `r[k] = Σ_{n=0}^{N−1−k} x[n+k]·conj(x[n])`, for lags `k = 0 … max_lag`.
  - This is NumPy's `correlate(x, x)` at lag `k`, and it makes `r[−k] = conj(r[k])`, so only
    lags `≥ 0` are returned.
  - `r[0]` is the energy `Σ|x|²`, and it is real.
  - A real input gives a real result, and a complex input gives a complex one.
- **The scaling.**
  - `"biased"`, the default, divides each lag by `N`. It keeps the sequence positive
    semidefinite, which Levinson-Durbin and PSD estimates need.
  - `"unbiased"` divides lag `k` by `N − k`.
  - `"none"` gives the raw sums.
- **The mean is kept.** Callers remove it first if they want the autocovariance.
- **The rules.**
  - The samples are 1-D and finite, with at least one of them.
  - `max_lag` is an integer from 0 to `N − 1`, and it defaults to `N − 1`. Python rejects
    floats and bools.
  - `scaling` is one of the three names.
  - Anything else is `invalid_argument`.

## Consequences

- **Cost.** The direct sum costs `O(N·max_lag)`, which is fine for the lags pitch and
  prediction use. An FFT form can be added later with the same results.
- **Vectors.** These are worked by hand in exact integers, then divided:
  - a real sequence under each scaling.
  - a complex sequence, which checks the conjugate side.
  - a short `max_lag`.
  - a single sample.
  - the errors.
- **Tests.**
  - The result matches a direct `O(N²)` sum over the full two-sided correlation.
  - A periodic signal peaks at its period.
  - `r[0]` equals the energy.
