# ADR 0084: Frequency-sampling FIR design

Status: accepted, 2026-11-13

## Context

Windowed sinc handles ideal bands only. Equiripple and least squares handle piecewise targets, but
each needs a solve. Frequency sampling is the direct way to get an arbitrary magnitude: sample the
target on a grid, take the inverse DFT, window it. Libraries differ in the details that change
the taps:
- how the target is described;
- the grid size;
- the phase given to the samples;
- how the Nyquist sample is treated for even lengths;
- whether the result is rescaled.

## Decision

- **`fir_frequency_sampling(num_taps, frequencies, gains, sample_rate, window="hamming",
  beta=None, num_points=None)`** (C# `Dsp.FirFrequencySampling`), beside the other FIR designs.
- **The target**: breakpoints `frequencies` in Hz, strictly increasing from exactly 0 to exactly
  `fs/2`, and one gain at each. The gain is linear in frequency between breakpoints. Strictly
  increasing means no duplicate points, so there are no vertical steps. A step is two close
  breakpoints, which keeps "the gain at a frequency" single-valued.
- **The grid**: `K = num_points` samples from 0 to `fs/2` inclusive, the DFT length is
  `L = 2(K − 1)`, and `L ≥ num_taps` is required so the taps do not alias. By default `K − 1` is the
  smallest power of two at least `max(num_taps, 512)`. The default does not depend on the
  language, and its grid is dense enough that the sampled target is close to the continuous one.
- **Phase**: the linear phase of a symmetric filter with delay `(N − 1)/2`. The taps are therefore
  the real closed form `d(t) = (1/L)[G_0 + 2 Σ G_k cos(2πkt/L) + G_{K−1} cos(πt)]` at
  `t = n − (N − 1)/2`. This is the definition; each language may evaluate it by FFT.
- **Even `num_taps`** (type II) has `cos(πt) = 0`, so it cannot honour a nonzero gain at `fs/2`.
  That raises instead of being silently dropped.
- **Exact symmetry**: the windowed taps are averaged with their reverse, so neither FFT round-off
  nor the window's own round-off can break linear phase.
- **No rescaling** after the window. The design's gain is the window-smoothed target, not
  normalized to a reference frequency. A flat target gives exactly the unit impulse, because the
  window's centre is 1 for odd lengths.
- Only symmetric types I and II. The antisymmetric types (differentiators, Hilbert) are left for
  later.
- **Expected values**:
  - a stdlib generator that evaluates the closed form by direct cosine sums, with its own
    interpolation and windows;
  - by-hand cases: the flat target, `N = 3, K = 3` on a ramp (`[1/4, 1/2, 1/4]`), and an even
    `N = 2` case.

## Consequences

- Taps agree across languages to FFT round-off (about `1e-16` times the largest gain).
- A user who wants the DFT samples hit exactly at the grid points can use the rectangular window
  with `num_points` chosen so `L = num_taps`. For `L > N` the samples are only approached.
