# ADR 0153: Minimum phase from the cepstrum

Status: accepted, 2026-11-16. It builds on the real cepstrum (ADR 0151).

## Context

Every magnitude spectrum has one minimum-phase sequence: the causal sequence with all its
zeros inside the unit circle, which packs its energy as early as possible. The homomorphic
method finds it from the real cepstrum. It folds the anticausal half onto the causal half and
exponentiates back. It is used to make minimum-phase filters from linear-phase ones, and as a
spectral factorisation. Implementations differ on four points:

- the fold for odd and even lengths;
- the FFT length;
- the output length;
- what happens to the imaginary residue.

## Decision

- **The API.**
  - Python: `minimum_phase(samples, nfft=None)`, returning `nfft` real values.
  - C#: `Spectral.MinimumPhase(samples, nfft)`, where `nfft` is an `int?`, returning `double[]`.
- **The value.**
  - `c = real_cepstrum(samples, M)` (ADR 0151), with `M = nfft`.
  - Then `ĉ` is the fold:
    - `ĉ[0] = c[0]`;
    - `ĉ[m] = 2c[m]` for `1 ≤ m ≤ ⌈M/2⌉ − 1`;
    - `ĉ[M/2] = c[M/2]` when `M` is even;
    - every other value is 0.
  - `y = Re IFFT(exp(FFT(ĉ)))`, and the rounding residue of the imaginary part is dropped.
- **The FFT length.**
  - The cepstrum of a finite sequence is infinitely long, so it aliases at `M` bins. The error
    falls off like `ρ^{M/2}`, where `ρ` is the largest zero radius after reflection.
  - So the default is not `N`. It is the smallest power of two that is at least `max(64, 8N)`.
  - An explicit `nfft` must be at least `N`.
- **The output length.** All `M` values are returned, and the tail past `N` is near zero. A
  caller who wants `N` taps slices them.
- **What is lost.** Only `|X|` is used, so the sign of the input is lost. `[−2, −0.5]` maps to
  `[2, 0.5]`.
- **The rules.**
  - Those of `real_cepstrum`: the samples are real and finite, at least one of them, with no
    spectrum bin exactly 0, so no zero on the unit circle at a bin.
  - `nfft ≥ N`.
  - Python rejects complex samples.

## Consequences

- **Vectors are analytic.** A factor `1 − z·z⁻¹` with `|z| > 1` has the same magnitude as
  `|z|·(1 − z̄⁻¹·z⁻¹)`. So the minimum-phase sequence is the product of the factors, each with
  its outside zeros reflected and scaled.
  - The generator multiplies these out in Fractions.
  - It checks that `ρ^{M/2}` is below `10^−16`, so the aliasing is far under the tolerance.
  - The cases are:
    - a minimum-phase pair, which maps to itself;
    - its time reverse;
    - a negative gain;
    - two zeros, one of them outside the circle;
    - the default `nfft`;
    - an odd `nfft`;
    - an impulse;
    - the errors.
- **Tests.**
  - The magnitude spectrum is kept.
  - Every partial energy `Σ_{n≤k} y²` is at least that of the input.
  - In Python, the zeros of the leading taps lie inside the unit circle.
