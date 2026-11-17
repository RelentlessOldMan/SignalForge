# ADR 0191: GCC-PHAT delay

Status: accepted, 2026-11-16. It goes with the cross-correlation of ADR 0190.

## Context

The generalized cross-correlation with phase transform (Knapp and Carter, 1976) estimates the
delay between two recordings. It whitens the cross-spectrum to unit magnitude, so the inverse
transform is a sharp peak at the delay whatever the spectra of the two signals. That makes it
robust to coloured sources and reverberation. Implementations differ on several points:

- the zero-padded length (and so whether the correlation wraps);
- what happens at bins where the cross-spectrum is zero;
- how far the search goes;
- interpolation;
- the sign of the delay.

## Decision

- **The API.** In `measurements`, for real input:
  - Python: `gcc_phat(x, y, sample_rate, *, max_delay=None)`, returning
    `GccPhat(delay, lag, peak)`.
  - C#: `Measurements.GccPhat(x, y, sampleRate, maxDelay = null)`.
- **The steps.**
  - With `N = len x` and `M = len y`, both signals are zero-padded to `L = N + M − 1`. This
    makes the circular correlation the linear one, with no wrap.
  - `G = X·conj Y`. `W = G/|G|` where `|G| > 0`, and 0 where `|G| = 0`.
  - `r = Re ifft(W)` (ADR 0006 scaling).
  - Circular index `i` is lag `i` for `i < N`, and lag `i − L` otherwise. The lag sign is that
    of `cross_correlation`: when `x` is a delayed `y` the lag is positive.
- **The search.**
  - Lags run from `−(M−1)` to `N − 1`.
  - `max_delay` (seconds, finite, ≥ 0) limits them to `|k| ≤ ⌊max_delay·fs⌋`.
  - `lag` is the largest `r`, and on a tie the smallest lag.
- **Refinement.**
  - When both neighbours are in the searched range and
    `c = r[lag−1] − 2r[lag] + r[lag+1] < 0`, the fraction is
    `δ = (r[lag−1] − r[lag+1])/(2c)`.
  - Otherwise `δ = 0`.
  - `delay = (lag + δ)/fs` seconds, and `peak = r[lag]`.
- **The rules.**
  - Both inputs are real, one-dimensional, finite, not empty and not all zero.
  - `sample_rate` is finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors.** They come from closed forms.
  - For impulses `x = a·δ[n−p]` and `y = b·δ[n−q]` with `a, b > 0`, `W = e^{−jω(p−q)}`
    exactly. So `r` is 1 at lag `p − q` and 0 elsewhere, `δ = 0` and the peak is 1. The
    vectors cover positive, negative and zero delays.
  - For `y = x`, `W = 1` wherever `X ≠ 0`.
  - The zero-bin case `x = [1, 1]`, `y = [1]` gives `W = [1, 0]` and `r = [½, ½]`, a tie
    that resolves to lag 0.
- **Unit tests.** Fractional delays are covered approximately, in unit tests.
