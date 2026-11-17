# ADR 0241: Moving average

Status: accepted, 2026-11-17.

## Context

A boxcar smoother is the plainest FIR lowpass. It is the CIC prototype without the integer
arithmetic, and the mean that the moving RMS (ADR 0239) takes the root of. Callers spell it as
`np.convolve(x, ones(N)/N)` and get different edges and rounding.

## Decision

- **The API.**
  - Python: `moving_average(samples, length)` in `dsp`.
  - C#: `Dsp.MovingAverage(samples, length)`, real or complex in, the same kind out.
- **The value.**
  - `y[n] = (1/N)·Σ_{k=n−N+1}^{n} x[k]`, with `x` zero before 0. The window starts from rest, and
    every output is divided by `N`.
  - Each sum is computed directly, oldest first, then divided by `N`. As in ADR 0239, there is no
    running sum.
- **The rules.**
  - `length` must be an integer `≥ 1`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - Exact rational means.
  - A constant `a` gives `a·min(n + 1, N)/N`.
  - A ramp `x[n] = n` gives `n − (N − 1)/2` once the window is full.
