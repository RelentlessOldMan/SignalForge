# ADR 0196: Two-sided cross-spectral density for complex input

Status: accepted, 2026-11-16. It extends ADR 0194.

## Context

`cross_spectral_density` (ADR 0194) took real input only, and gave only the one-sided result.
Baseband (IQ) work needs the two-sided `Pxy` of complex signals, in the same shifted order that
`welch_psd` uses for complex samples.

## Decision

- **The API.**
  - Python: `cross_spectral_density` gains `one_sided: bool | None = None`, with the same
    meaning as in `welch_psd`:
    - `None` gives one-sided when both inputs are real, and two-sided otherwise.
    - `True` with any complex input is `invalid_argument`.
    - `False` gives two-sided for real input too.
  - C#:
    - The real overload gains `oneSided = true`, as its last parameter.
    - A new `Complex` overload is always two-sided. It is used when either input is complex;
      the real side is then widened.
- **The two-sided result.**
  - `Pxy[k] = Σ_s conj X_s[k]·Y_s[k] / (K·fs·Σw²)` for every bin `k = 0 … M−1`, with no
    doubling.
  - The bins are returned in `fftshift` order, with frequencies from
    `fft_frequencies(M, fs, shifted=True)`, as `welch_psd` returns them.
  - For `y = x` this is the complex `welch_psd`.
- **The one-sided result.** It is unchanged from ADR 0194.
- **The rules.** They are otherwise those of ADR 0194: one-dimensional, finite, the same length,
  and the `welch_psd` segment rules.

## Consequences

- **Vectors.** They are hand DFTs of short rectangular segments, with the shifted order worked
  out by hand:
  - a complex pair;
  - a real and complex pair;
  - real input with `one_sided=False`;
  - two complex segments.
- **One untested case.** C# has no form of `one_sided=True` with complex input, as with
  `welch_psd`. That error is covered by a Python unit test, not by a vector.
