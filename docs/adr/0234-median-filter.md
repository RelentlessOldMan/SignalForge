# ADR 0234: Running median filter

Status: accepted, 2026-11-17.

## Context

A running median removes impulsive noise (spikes, clicks, dropouts) while keeping edges sharp,
which no linear filter can do. The only choice in it is what to do at the ends.

## Decision

- **The API.**
  - Python: `median_filter(samples, length)` in `dsp`.
  - C#: `Dsp.MedianFilter(samples, length)`, for real samples.
- **The value.**
  - With `h = (length − 1)/2`, output `n` is the median of `x[n − w … n + w]`, where
    `w = min(h, n, L − 1 − n)`.
  - The window is symmetric, and it shrinks near the ends so that it stays inside the data.
  - The window always holds an odd number of samples, so the output is always one of the input
    samples. In particular `y[0] = x[0]` and `y[L−1] = x[L−1]`.
  - There is no zero-padding, which would pull the ends towards 0, and no reflection.
- **The rules.**
  - `length` must be an odd integer `≥ 1`.
  - The samples must be real, finite and non-empty. Any length is allowed, even shorter than
    `length`.

## Consequences

- **Vectors.** The expected values are the middle element of each sorted window, which is exact.
