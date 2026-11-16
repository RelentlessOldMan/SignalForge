# ADR 0151: Real cepstrum

Status: accepted, 2026-11-16.

## Context

The real cepstrum is the inverse transform of the log magnitude spectrum. It separates a
smooth spectral envelope, which sits at low quefrencies, from a periodic excitation, which
shows as a peak at the period. It is also the first step of minimum-phase reconstruction.
Implementations differ on four points:

- the log base;
- the FFT length;
- what happens to a zero bin;
- how much of the result is returned.

## Decision

- **The API.**
  - Python: `real_cepstrum(samples, nfft=None)`, returning a real array of `nfft` values.
  - C#: `Spectral.RealCepstrum(samples, nfft)`, where `nfft` is an `int?`, returning
    `double[]`.
- **The value.**
  - `c[m] = (1/M)·Σ_k ln|X[k]|·e^{+j2πkm/M}`, where `X` is the `M = nfft`-point FFT of the
    samples, zero padded.
  - The log is natural.
  - `ln|X|` is real and even, so `c` is real. The rounding residue of the imaginary part is
    dropped.
  - The full `M` values are returned. Quefrency `m` is `m / fs` seconds, and the second half
    mirrors the first.
- **The FFT length.** `nfft ≥ N`, and it defaults to `N`. Any length works, as for `fft`.
- **Zero bins.** A bin whose magnitude is exactly 0 is `invalid_argument`. No floor is
  applied: a floor would change the result by an amount that depends on its value. Callers
  who want one add it to the spectrum, or add a little noise, first.
- **The rules.**
  - The samples are 1-D, real and finite, with at least one of them.
  - `nfft` is an integer `≥ N`. Python rejects floats and bools.
  - Python rejects complex samples.

## Consequences

- **Phase is discarded.** A signal and its time reverse, or any delay of it, have the same real
  cepstrum.
- **Vectors.** These come from the series
  `ln|1 + a·e^{−jω}| = Σ_{n≠0} (−1)^{|n|+1} a^{|n|} / (2|n|)·e^{−jnω}` for `|a| < 1`.
  - With a gain `g`, `x = g·(δ + a·δ[n−1])` has `c_∞[0] = ln|g|` and
    `c_∞[n] = (−1)^{|n|+1} a^{|n|}/(2|n|)` for `n ≠ 0`.
  - Sampling at `M` bins aliases it: `c[m] = Σ_j c_∞[m + jM]`.
  - The generator sums the series in Fractions until the tail is below `2^−300`.
  - The cases are a minimum-phase pair, its time reverse (the same result), a negative `a`, a
    gain, the default `nfft`, an impulse, a delay, and the errors.
- **Tests.**
  - A pulse train's cepstrum peaks at its period.
  - The result is real and even.
  - Python rejects complex input.
