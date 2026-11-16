# ADR 0159: Cepstral liftering

Status: accepted, 2026-11-16. It adds the liftering that ADR 0157 left out of MFCC.

## Context

The higher cepstral coefficients are small. HTK's sinusoidal lifter rescales them so that they
have comparable magnitudes:

`c'_n = (1 + (L/2)·sin(π n / L))·c_n`.

Implementations differ on:

- the name of `L`;
- whether `L = 0` means no lifter;
- whether there is an inverse.

## Decision

- **The API.**
  - Python: `cepstral_lifter(coefficients, length=22)`, in `spectral`.
  - C#: `Spectral.CepstralLifter(ReadOnlySpan<double> coefficients, int length = 22)`.
  - It takes one frame of coefficients `c_0, c_1, …` and returns the same length.
  - It is a separate function, so `mfcc` keeps its signature.
- **The formula.** `c'_n = (1 + (L/2)·sin(π n / L))·c_n`, so `c_0` is unchanged.
- **The rules.**
  - The coefficients are 1-D, real and finite, with at least one value.
  - `length` is an integer of at least 1. There is no `L = 0` meaning "none": not calling the
    function means none.
  - Anything else is `invalid_argument`.
- **No inverse.** For `n > L` the weight `1 + (L/2)·sin(π n / L)` can be zero, so an inverse
  is not always defined.

## Consequences

- **The default.** `L = 22` matches HTK's usual setting.
- **`L = 1`.** `sin(π n)` is 0, so every weight is 1.
- **Vectors are exact.** They use `L = 12`, where `sin(kπ/12)` is exact (`(√6 − √2)/4`, `1/2`,
  `√2/2`, `√3/2`, `(√6 + √2)/4`, `1`), with `n` up to 14 to cover the negative half. There are
  also `L = 2`, `L = 1`, the default, and the errors.
