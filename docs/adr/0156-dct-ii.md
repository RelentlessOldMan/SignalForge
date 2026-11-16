# ADR 0156: DCT-II and its inverse

Status: accepted, 2026-11-16.

## Context

The type-II discrete cosine transform decorrelates log filterbank energies into MFCCs. It is
also the usual "DCT" of compression. Libraries differ on three points:

- the scaling, where SciPy's default is `2Σ` and the orthonormal scaling is also common;
- what `idct` means: the plain DCT-III, or the exact inverse;
- how it is computed.

## Decision

- **The API.**
  - Python: `dct(samples, *, orthonormal=True)` and `idct(coefficients, *, orthonormal=True)`,
    in `spectral`.
  - C#: `Spectral.Dct(samples, orthonormal = true)` and `Spectral.Idct(coefficients,
    orthonormal = true)`.
- **The forward transform.**
  - Orthonormal (the default): `X[k] = s_k·Σ_n x[n]·cos(π k (2n+1) / (2N))`, with
    `s_0 = √(1/N)` and `s_k = √(2/N)` for `k ≥ 1`.
  - Unnormalized: `X[k] = 2·Σ_n x[n]·cos(π k (2n+1) / (2N))`, the same as SciPy's `norm=None`.
- **The inverse.** `idct` is always the exact inverse of `dct` with the same `orthonormal`. It
  is a DCT-III:
  - orthonormal: `x[n] = Σ_k s_k·X[k]·cos(π k (2n+1) / (2N))`;
  - unnormalized: `x[n] = (1/N)·(X[0]/2 + Σ_{k≥1} X[k]·cos(π k (2n+1) / (2N)))`.
  - This differs from SciPy, whose unnormalized `idct` needs a further `1/(2N)`.
- **How it is computed.**
  - Directly, in `O(N²)`. The cosines come from one table, `cos(π j / (2N))` for
    `j = 0 … 4N − 1`, indexed by `k(2n+1) mod 4N`. So both languages use the same cosine
    values, and symmetric entries are equal.
  - MFCC lengths are tens of values, so this is fast enough. An FFT path can be added later
    behind the same API.
- **The rules.**
  - The input is 1-D, real and finite, with at least one value.
  - Python rejects complex input.

## Consequences

- **Orthonormal is an orthogonal matrix.** It keeps energy, and `idct(dct(x)) = x`.
- **Vectors are hand-worked.** The exact values use `√2`, `cos(π/8) = √(2+√2)/2` and
  `cos(3π/8) = √(2−√2)/2`, computed in 50-digit `decimal`. The cases are:
  - `N = 1`;
  - a constant, which maps to `k = 0` only;
  - `[1, 0]`;
  - an impulse at `n = 1` with `N = 4`;
  - the basis vector `m = 1` with `N = 4`, which maps to `√(N/2)` at `k = 1` alone;
  - each case in both scalings, and each inverse;
  - the errors.
- **Tests.**
  - Round trips in both scalings.
  - Energy is kept under the orthonormal scaling.
  - The orthonormal matrix times its transpose is the identity.
