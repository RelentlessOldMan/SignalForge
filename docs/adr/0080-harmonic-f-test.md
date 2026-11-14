# ADR 0080: Thomson's harmonic F-test for line components

Status: accepted, 2026-11-13

## Context

A PSD shows a sinusoid in colored noise as a peak, but the PSD alone doesn't say whether a peak
is a line or a bump in the noise. Thomson (1982) tests each frequency separately. If the input
holds a line `μ·e^{2πi f t}` at frequency `f`, every eigencoefficient there is
`X_j(f) = μ·U_j + noise`, with `U_j = Σ_n v_j[n]` the taper's DC value. A regression of the `X_j`
on the `U_j` estimates `μ`. The F statistic is the power the regression explains over the power
left in the residual. With Gaussian noise that is smooth across `[f − W, f + W]`, it has an
F(2, 2K − 2) distribution when there is no line. The multitaper code (ADRs 0078, 0079) already
computes the `X_j`.

## Decision

- `harmonic_f_test(samples, sample_rate, half_bandwidth, *, num_tapers=None, nfft=None)` →
  `HarmonicFTest(frequencies, amplitudes, f_statistic, p_values, num_tapers)`. In C#,
  `Spectral.HarmonicFTest(...)` returns the record `HarmonicFTestResult`, because the method and
  the record can't share a name in a readable way, and a `Result` suffix is clearer than a
  different word.
- Per bin, using the same tapers and DFTs as `multitaper_psd`:
  - `μ = Σ_j U_j X_j / Σ_j U_j²`;
  - `F = (K − 1)·|μ|²·Σ_j U_j² / Σ_j |X_j − μ U_j|²`;
  - `p = (1 + F/(K − 1))^−(K−1)`, the exact upper tail of F(2, 2K − 2). It needs no special
    function: the F(2, ν) survival function is `(1 + 2F/ν)^−ν/2`.
- `U_j` is the taper's computed sum. The odd tapers' sums are 0 up to rounding, so they count
  only in the residual, as in Thomson's test.
- When the residual is exactly 0, `F` is `+∞` and `p` is 0, unless `μ` is 0 too (all-zero
  input). Then `F` is 0 and `p` is 1.
- `μ` is the complex amplitude at `t = n` (samples from 0), so `a·cos(2π f n/fs + φ)` gives
  `μ ≈ (a/2)·e^{iφ}` at `+f`. A complex line `A·e^{2πi b n/M}` at an exact bin gives `μ = A`
  exactly.
- Real input gives the bins `0 … ⌊M/2⌋` with `f = b·fs/M`. Complex input gives all `M` bins on
  the two-sided axis of the PSD (`−⌊M/2⌋ …`). Nothing is folded: an amplitude is not a density.
- `K ≥ 2` is required, because with one taper the residual has no degrees of freedom. An
  explicit `num_tapers=1`, or a default count of 1 (`2NW < 3`), is an argument error.

## Not now

Line removal (subtracting `μ`'s line and reshaping the PSD), and Thomson's jackknife variance.

## Consequences

Expected values come from a stdlib generator. It computes the regression from its own Jacobi
tapers and direct DFTs. There are also by-hand cases:

- N = 2, x = (3, 1) with tapers `(1, ±1)/√2`: μ = (2, 1), F = (4, 0.25), p = (0.2, 0.8).
- All-zero input: μ = 0, F = 0, p = 1.

The tests check that an exact-bin complex line gives `μ = A`, and that under white noise the
p-values are close to uniform.
