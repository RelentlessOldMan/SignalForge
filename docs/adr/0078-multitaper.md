# ADR 0078: DPSS tapers and the multitaper PSD

Status: accepted, 2026-11-13

## Context

Welch's method trades resolution for variance by cutting the record into segments. Thomson's
multitaper method keeps the whole record and averages the spectra of the record under `K`
orthogonal tapers instead, the discrete prolate spheroidal sequences (Slepian), which hold the
most energy inside a chosen band `[−W, W]`. The first taper leaks far less than the usual windows
at the same resolution (at NW 4, 4e-11 of the peak 6 bins out, where Hann leaks 1e-6); the plain
average over all `2NW − 1` tapers leaks near the rectangular window's level, because the last
taper keeps only about 94% of its energy in the band (measured; [ADR 0079](0079-adaptive-multitaper.md)
weights them adaptively). The estimate has about `2K` degrees of freedom.

## Decision

- `dpss_tapers(length, half_bandwidth, num_tapers=None)` in `spectral` (C#
  `Spectral.DpssTapers`) returns `TaperSet(tapers, concentrations)` (not `Tapers`: a C# record
  cannot have a property of its own name): `K` rows of `N` values and the fraction of each
  taper's energy inside `[−W, W]`, `W = NW/N`, `NW = half_bandwidth` (the time–half-bandwidth
  product). `K` defaults to `max(1, ⌊2NW⌋ − 1)`.
- The tapers are the eigenvectors of the symmetric tridiagonal matrix that commutes with the
  band-limiting (sinc) matrix, for its `K` largest eigenvalues: they are the sinc matrix's
  eigenvectors too, but well conditioned where the sinc matrix's eigenvalues crowd at 1. The
  method is ours to choose; the result is fixed: unit energy, a sign rule, largest
  concentration first.
- Solved by Sturm-sequence bisection for each eigenvalue and inverse iteration for its vector
  (tridiagonal, `O(N)` per step), in plain loops in both languages. No dense `N × N` matrix, so
  long records are fine. NumPy's `eigh` would need the dense matrix; it is not used.
- The concentrations are computed from the definition (the quadratic form of the sinc matrix,
  through the taper's autocorrelation), not from the tridiagonal eigenvalues, which are a
  different quantity.
- `multitaper_psd(samples, sample_rate, half_bandwidth, *, num_tapers=None, one_sided=None,
  nfft=None)` (C# `Spectral.MultitaperPsd`, real and complex) returns the Welch
  `SpectralDensity`: the plain mean of the `K` tapered periodograms, scaled, folded and with the
  frequency axis exactly as `welch_psd` with one segment. `num_segments` is `K` (the spectra
  averaged), `enbw_hz` is `2W·fs`, the band each estimate averages over.
- Not now: Thomson's adaptive weights, the F-test for line components, and the
  concentration-weighted mean. Each is a later option on the same tapers.

## Expected values

The vector generator solves the tridiagonal problem in the standard library and checks each taper
against the definition: `A·v = λ·v` with `A` the sinc matrix built directly, to `1e-10`, and the
tapers orthonormal. `N = 1` and `N = 2` are by hand. The PSD cases take a direct DFT of each
tapered record.
