# ADR 0197: Complex input for coherence and the transfer functions

Status: accepted, 2026-11-16. It extends ADRs 0192, 0193 and 0195, as ADR 0196 extended the
cross-spectral density.

## Context

`coherence`, `transfer_function` (H1) and `transfer_function_h2` took real input only.
Baseband (IQ) channels and complex systems need them for complex samples, where positive and
negative frequencies differ.

## Decision

- **Complex input.** When `x` or `y` is complex, the three functions use all `M` bins of the
  segment FFTs. The bins are in `fftshift` order, with `fft_frequencies(M, fs, shifted=True)`,
  as `welch_psd` and `cross_spectral_density` use for complex samples.
- **Real input.** It is unchanged: one-sided bins `0 … ⌊M/2⌋`.
- **No `one_sided` argument.** Coherence and the transfer functions are ratios, and doubling
  cancels in a ratio. A real input gives the same values on its one-sided bins either way, so
  there is no reason to ask for the two-sided form.
- **The rules.** The definitions and NaN rules are unchanged, applied per bin:
  - coherence: `min(1, |Sxy|²/(Sxx·Syy))`, NaN where an auto-spectrum is 0;
  - H1: `Sxy/Sxx`, complex NaN where `Sxx = 0`;
  - H2: `Syy/conj Sxy`, complex NaN where `Sxy = 0`.

  Inputs must be one-dimensional, finite and the same length. A real input paired with a
  complex one is widened.
- **C#.** `Spectral.Coherence`, `Spectral.TransferFunction` and `Spectral.TransferFunctionH2`
  gain `ReadOnlySpan<Complex>` overloads.

## Consequences

- **The vectors** are hand DFTs of length-2 complex segments, in shifted order:
  - `y = (1+j)·x` gives `H1 = H2 = 1+j` and coherence 1;
  - a single complex segment gives `H = Y/X`;
  - two segments that disagree: H1 is 0, H2 is NaN and the coherence is 0 on one bin;
  - a real and complex pair.
- **One shared helper.** All four cross-spectral functions now share it, with each language's
  own copy: Python `_cross_segments`, C# `CrossSegments`.
