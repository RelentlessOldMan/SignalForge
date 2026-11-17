# ADR 0190: Cross-correlation

Status: accepted, 2026-11-16. It goes with the autocorrelation of ADR 0148.

## Context

Cross-correlation is the basis for:

- delay estimation;
- matched filtering;
- alignment of two recordings.

Conventions differ in three ways:

- which signal is conjugated;
- the sign of the lag;
- whether the result is scaled.

`autocorrelation` (ADR 0148) already fixed `r[k] = Σ x[n+k]·conj x[n]`, which is NumPy's
`correlate(x, x)`.

## Decision

- **The API.** In `dsp`:
  - Python: `cross_correlation(x, y)`.
  - C#: `Dsp.CrossCorrelation(x, y)`.
- **The definition.** `r[k] = Σ_n x[n+k]·conj y[n]`, summed over the `n` where both indices
  are in range, for `k = −(M−1) … N−1`, with `N = len x` and `M = len y`.
  - The result has `N + M − 1` values, with lag `k` at index `k + M − 1`. Lag 0 is at
    `M − 1`.
  - A positive lag means that `x` is later than `y`: if `x[n] = y[n − d]`, the peak is at
    lag `d`.
  - This is NumPy's `correlate(x, y, "full")`. For `y = x` the lags from 0 up are the
    unscaled `autocorrelation`.
- **Scaling.** None. A caller divides as they need.
- **Types.**
  - Two real inputs give a real result.
  - Otherwise both inputs are taken as complex and the result is complex. C# has a real pair
    and a complex pair of overloads.
- **The rules.**
  - Both inputs are one-dimensional, finite and not empty.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors.** They are hand sums:
  - lengths `N > M`, `N < M` and `1 × 1`;
  - a delayed impulse, whose peak sits at the delay;
  - a complex case that checks the conjugate;
  - a mixed real and complex case.
