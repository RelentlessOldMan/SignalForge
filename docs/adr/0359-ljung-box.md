# ADR 0359: Ljung–Box statistic

Status: accepted, 2026-11-18.

## Context

The Ljung–Box test (Ljung and Box, 1978) asks whether a record is white. It is the usual check
on the residuals of a fitted model. It sums the squared sample autocorrelations over the first
`h` lags, with weights that improve on Box and Pierce's plain sum in short records.

## Decision

- **The API.**
  - Python: `ljung_box(samples, lags)` in `measurements`, giving a float.
  - C#: `Measurements.LjungBox(ReadOnlySpan<double> samples, int lags)`.
- **The value.**
  - With `x̄` the mean, the sample autocorrelation is
    `ρ_k = Σ_{t=0}^{N−k−1} (x_t − x̄)(x_{t+k} − x̄) / Σ_t (x_t − x̄)²`. This is the biased form.
  - The value is `Q = N(N + 2) Σ_{k=1}^{h} ρ_k²/(N − k)`.
  - Under the null of white noise, `Q` is about chi-squared with `h` degrees of freedom, less
    any fitted parameters. SignalForge does not give the p-value. It would need the
    incomplete gamma function, and the degrees of freedom are the caller's choice.
- **The rules.**
  - `samples` real, one-dimensional and finite, and not all equal.
  - `lags` an integer from 1 to `N − 1`.

## Consequences

- **Vectors.**
  - The samples are dyadic, so the generator takes the mean, every `ρ_k` and `Q` exactly in
    rationals.
  - The tolerance is `abs 1e-12, rel 1e-12`.
