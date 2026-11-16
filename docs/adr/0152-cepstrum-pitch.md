# ADR 0152: Cepstrum pitch

Status: accepted, 2026-11-16. It builds on the real cepstrum (ADR 0151) and follows the
autocorrelation pitch (ADR 0150).

## Context

A periodic excitation, or an echo, puts a peak in the real cepstrum at its period. The spectral
envelope stays at low quefrencies. Picking the highest peak in a quefrency range is the classic
cepstral pitch detector. It is less prone to octave errors than the autocorrelation when the
envelope has strong formants. Choices to fix:

- the quefrency range;
- refinement;
- what is reported besides the frequency;
- the FFT length.

## Decision

- **The API.**
  - Python: `cepstrum_pitch(samples, sample_rate, min_frequency, max_frequency, nfft=None)`,
    returning `CepstrumPitch(frequency, quefrency, strength)`.
  - C#: `Measurements.CepstrumPitch(samples, sampleRate, minFrequency, maxFrequency, nfft)`,
    returning the record of the same name.
- **The cepstrum.** `c = real_cepstrum(samples, nfft)` (ADR 0151). `M = nfft`, which defaults
  to `N`.
- **The quefrency range.**
  - It runs from `lo = ceil(fs / max_frequency)` to `hi = floor(fs / min_frequency)`, the same
    rule as ADR 0150.
  - It must satisfy `lo ≤ hi` and `2·hi < M`, so the range stays in the first half and every
    quefrency has a right neighbour.
- **The peak and the refinement.** These follow ADR 0150 exactly:
  - `L` is the largest `c[L]` in the range, and ties go to the smallest quefrency.
  - The parabola `δ = (c[L−1] − c[L+1]) / (2(c[L−1] − 2c[L] + c[L+1]))` applies only when
    `c[L]` is at least both neighbours and the curvature is negative. Otherwise `δ = 0`.
  - The two pitch functions share one private helper in each language.
- **The value.**
  - `quefrency = L + δ` samples, and `frequency = fs / quefrency` Hz.
  - `strength = c[L]` at the integer quefrency, in nepers of log magnitude. It has no fixed
    range.
- **The rules.**
  - Those of `real_cepstrum`, including that a zero bin is `invalid_argument`.
  - `sample_rate` is finite and positive.
  - `0 < min_frequency ≤ max_frequency`, both finite.
  - The range is not empty and fits as above.

## Consequences

- **Echo detector.** An echo `x = δ + a·δ[n−P]` gives `c_∞[±kP] = (−1)^{k+1} a^k / (2k)`, so
  the cepstrum peaks at `P` for `0 < a < 1`.
- **Vectors.** The cepstra are exact from the Fractions series of ADR 0151, generalised to a
  tap at `P`, with aliasing at `M`. So the peak, `δ` and the strength are exact before the
  final rounding. The cases are:
  - an echo (whose neighbours carry only tiny aliased terms);
  - an adjacent two-tap at `a = 1/2` with a range that skips the first lags, so the parabola
    moves the peak noticeably;
  - a negative `a`, whose cepstrum rises through the range, so the peak sits at the edge with
    no refinement;
  - an impulse, whose cepstrum is all zero, a tie that gives `lo` with `δ = 0`;
  - the errors.
- **Tests.**
  - A pulse train through a short filter is found at its period.
  - Scaling only shifts `c[0]`, so it leaves the result unchanged.
  - Python rejects complex input.
