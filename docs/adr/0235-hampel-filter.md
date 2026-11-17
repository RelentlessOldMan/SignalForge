# ADR 0235: Hampel outlier filter

Status: accepted, 2026-11-17. It builds on ADR 0234 (the running median filter).

## Context

A running median changes every sample. The Hampel filter replaces only the samples that are
outliers, judged by a robust local scale estimate, and passes all the others through unchanged.

## Decision

- **The API.**
  - Python: `hampel_filter(samples, length, threshold=3.0)` in `dsp`.
  - C#: `Dsp.HampelFilter(samples, length, threshold = 3)`, for real samples.
- **The windows.** They are the windows of ADR 0234: `x[n − w … n + w]`, with
  `w = min(h, n, L − 1 − n)` and `h = (length − 1)/2`.
- **The value.**
  - `m_n` is the median of the window. `MAD_n` is the median of `|x_j − m_n|` over the window.
  - The scale is `σ_n = κ·MAD_n`, with `κ = 1/Φ⁻¹(3/4) = 1.482602218505602`. This makes `σ` a
    consistent estimate of the standard deviation for Gaussian data.
  - `y[n] = m_n` if `|x[n] − m_n| > (threshold·κ)·MAD_n`, and `y[n] = x[n]` otherwise. The test is
    strict.
  - With `MAD_n = 0`, any sample that differs from the median is replaced.
  - With `threshold = 0`, the result is the running median.
  - The end samples always pass through unchanged, because their windows hold only themselves.
- **The rules.**
  - `length` must be an odd integer `≥ 1`.
  - `threshold` must be finite and `≥ 0`.
  - The samples must be real, finite and non-empty.

## Consequences

- **Vectors.** The generator uses sorted windows, which give exact medians. It computes `κ` from
  `statistics.NormalDist().inv_cdf(0.75)` and checks it against the constant above. The
  threshold boundaries in the cases are kept well away from equality.
