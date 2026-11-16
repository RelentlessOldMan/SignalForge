# ADR 0150: Autocorrelation pitch

Status: accepted, 2026-11-16. It builds on the autocorrelation (ADR 0148).

## Context

A periodic signal correlates with itself at a delay of one period. Picking the highest
autocorrelation peak in a lag range estimates the fundamental directly from the samples. It
needs no spectral tones, unlike `harmonic_series` (ADR 0139). Implementations differ on four
points:

- the scaling, where `unbiased` treats every multiple of the period alike and invites
  sub-harmonic errors;
- how the lag range follows from the frequency range;
- how the lag is refined;
- what is reported about voicing.

## Decision

- **The API.**
  - Python: `autocorrelation_pitch(samples, sample_rate, min_frequency, max_frequency)`,
    returning `AutocorrelationPitch(frequency, lag, voicing)`.
  - C#: `Measurements.AutocorrelationPitch`, returning the record of the same name.
- **The correlation.** The `biased` autocorrelation of ADR 0148, which falls off with lag, so
  among the multiples of the period the shortest wins. The mean is not removed.
- **The lag range.**
  - It runs from `lo = ceil(fs / max_frequency)` to `hi = floor(fs / min_frequency)`, so every
    lag in it has `fs/lag` inside the frequency range.
  - It must satisfy `lo ≤ hi ≤ N − 2`, so that every lag has a right neighbour.
- **The peak.** `L` is the lag in `lo … hi` with the largest `r[L]`, and ties go to the
  smallest lag.
- **The refinement.**
  - If `r[L] ≥ r[L−1]` and `r[L] ≥ r[L+1]`, and the curvature
    `c = r[L−1] − 2r[L] + r[L+1]` is negative, then the parabola through the three points gives
    `δ = (r[L−1] − r[L+1]) / (2c)`, with `|δ| ≤ 1/2`.
  - Otherwise `δ = 0`. This covers a flat top, or a range edge where the correlation is still
    rising.
- **The value.**
  - `lag = L + δ` samples, and `frequency = fs / lag` Hz.
  - `voicing = r[L] / r[0]`, at the integer lag, from −1 to 1.
- **The rules.**
  - The samples are 1-D, real and finite, with at least 3 of them and energy above 0.
  - `sample_rate` is finite and positive.
  - `0 < min_frequency ≤ max_frequency`, both finite.
  - The lag range is not empty and fits as above.
  - Anything else is `invalid_argument`. Python also rejects complex samples.

## Consequences

- **Frame-based.** This is one estimate per call, so callers frame long signals themselves.
- **Exact cases.** The peak, `δ` and the voicing are ratios of autocorrelation sums, so integer
  samples give exact Fractions.
- **Vectors.** The generator works them from the definition in Fractions, and checks the hand
  values of the simple cases:
  - a symmetric peak.
  - an asymmetric peak, which tests the parabola.
  - a range edge with no refinement.
  - a tie.
  - the errors.
- **Tests.**
  - A sampled sine of known non-integer period is recovered to well under a percent.
  - Scaling the signal leaves the result unchanged.
