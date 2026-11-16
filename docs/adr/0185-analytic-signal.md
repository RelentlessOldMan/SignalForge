# ADR 0185: Analytic signal

Status: accepted, 2026-11-16.

## Context

The analytic signal `x + j·H{x}` of a real signal has an envelope `|·|`, an instantaneous phase
and an energy-time curve. The usual discrete form zeroes the negative-frequency DFT bins and
doubles the positive ones. Implementations differ on three points:

- the weights for the DC and Nyquist bins;
- odd lengths;
- what input is allowed.

## Decision

- **The API.** In `spectral`:
  - Python: `analytic_signal(samples)`.
  - C#: `Spectral.AnalyticSignal(samples)`.
  - The result is complex and as long as the input.
- **The definition.** `z = ifft(X·W)`, with `X = fft(x)` (ADR 0006 scaling) and these
  weights:
  - `W[0] = 1`;
  - `W[k] = 2` for `0 < 2k < N`;
  - `W[N/2] = 1` when `N` is even;
  - `W[k] = 0` for `2k > N`.

  This is the weighting of Marple (1999), "Computing the discrete-time analytic signal via FFT".
- **What follows from it.**
  - `Re z = x` up to rounding.
  - `N = 1` returns the sample.
  - DC and the Nyquist bin carry no imaginary part.
- **The rules.**
  - The input is real, one-dimensional, finite and not empty.
  - Anything else is `invalid_argument`.
  - Complex input is rejected rather than having its negative frequencies silently dropped.

## Consequences

- **Vectors.** They come from closed forms and hand DFT sums:
  - `cos θₙ → e^{jθₙ}` and `sin θₙ → −j·e^{jθₙ}` at bin frequencies, for even and odd `N`;
  - DC plus Nyquist, which stays real;
  - impulses of length 3 and 4, worked by hand.
