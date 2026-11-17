# ADR 0231: Sliding DFT

Status: accepted, 2026-11-17. It sits beside ADR 0224 (Goertzel).

## Context

Goertzel (ADR 0224) gives one DFT value for a whole block. Tracking one bin sample by sample over
a moving window, for tone detection with low latency or a running spectrum line, needs the
sliding DFT. Its recursion costs one complex multiply per output.

## Decision

- **The API.**
  - Python: `sliding_dft(samples, length, k)` in `spectral`.
  - C#: `Spectral.SlidingDft(samples, length, k)`, for real or complex samples.
  - Both return one complex value per input sample.
- **The value.**
  - With `N = length` and `x` zero before 0, output `n` is the DFT bin `k` of the `N` samples
    ending at `n`: `S_n = Σ_{m=0}^{N−1} x[n − N + 1 + m]·e^(−2πi k m/N)` for `n = 0 … L−1`.
  - For `n ≥ N − 1` this equals `fft(x[n−N+1 … n])[k]`. Before that, the window is padded with
    zeros at the front.
- **The algorithm.**
  - `S_n = ((S_{n−1} + x[n]) − x[n−N])·w`, with `S_{−1} = 0`, `w = cos θ + i sin θ` and
    `θ = 2πk/N`.
  - The recursion is marginally stable, with its pole on the unit circle. Round-off accumulates
    like a random walk, about `√L` ulps after `L` samples. It is not damped. A damping factor
    would change the value, so none is applied.
- **The rules.**
  - The samples must be finite and non-empty.
  - `length` must be an integer `≥ 1`.
  - `k` must be an integer in `0 … length − 1`.

## Consequences

- **Vectors.** The expected values are direct DFT sums over each window, computed in the
  generator without the recursion. They are cross-checked against closed forms:
  - a constant at `k = 0` gives the running count;
  - a complex exponential on bin `k` gives `N·e^(2πik(n−N+1)/N)` once the window is full.
