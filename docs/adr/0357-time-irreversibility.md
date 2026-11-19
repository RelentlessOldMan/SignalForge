# ADR 0357: Time irreversibility

Status: accepted, 2026-11-18.

## Context

A process is time-reversible when its statistics are the same played backwards. Linear
Gaussian processes are, so a test of irreversibility is a test against them, as surrogate
methods use. The simplest statistic, used in the surrogate-data literature (Schreiber and
Schmitz, 2000), is the skewness of the increments `x_{t+τ} − x_t`. It changes sign when the
record is reversed, and its mean is 0 for a reversible process.

## Decision

- **The API.**
  - Python: `time_irreversibility(samples, lag=1)` in `measurements`, giving a float.
  - C#: `Measurements.TimeIrreversibility(ReadOnlySpan<double> samples, int lag = 1)`.
- **The value.**
  - The increments are `Δ_t = x_{t+τ} − x_t` for `t = 0 … N − τ − 1`.
  - With `M_k` the mean of `Δ^k`, the value is `M_3/(M_2·√M_2)`, computed in that form.
  - Reversing the record negates it.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `lag` an integer from 1 to `N − 1`.
  - `M_2` must be above 0, so not every increment may be 0.

## Consequences

- **Vectors.**
  - The samples are dyadic. The generator takes `M_2` and `M_3` exactly in rationals, then
    the square root and the quotient in float.
  - The tolerance is `abs 1e-13, rel 1e-12`.
