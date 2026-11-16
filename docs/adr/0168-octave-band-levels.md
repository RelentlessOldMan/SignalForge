# ADR 0168: Octave-band levels

Status: accepted, 2026-11-16. It builds on the fractional-octave bands (ADR 0167) and the band
Butterworth (ADR 0016).

## Context

An octave-band analyser filters a signal through one band-pass per fractional-octave band and
reports each band's mean power. Implementations differ on four points:

- the filter, and its order;
- how bands at or above Nyquist are handled;
- whether the filter's start transient is skipped;
- the shape of the result.

## Decision

- **The API.** In `measurements`:
  - Python: `octave_band_levels(samples, sample_rate, fraction, min_frequency,
    max_frequency, *, order=3)`.
  - C#: `Measurements.OctaveBandLevels(samples, sampleRate, fraction, minFrequency,
    maxFrequency, order = 3)`, for real and complex samples, returning `double[]`.
  - The result has one mean power per band of `octave_bands(fraction, min_frequency,
    max_frequency)`, in the same order. The caller pairs them with the bands and takes dB.
- **The filter.** Each band uses `butterworth_bandpass(order, lower, upper, sample_rate)` with
  that band's edges. It has gain exactly `1/2` in power at the edges and `1` at the warped
  center. Order 3 (filter order 6) is the usual class-1 design.
- **The filtering.** The filter starts from rest (`IirFilter`, zero state) and runs over the whole
  input. The power is the mean of `|y|²` over every output sample; no transient is skipped.
  A caller who wants to skip it trims the input or pads it.
- **The rules.**
  - The samples are real or complex, one-dimensional, finite and not empty.
  - Every selected band's upper edge must be below `sample_rate / 2`; otherwise it is
    `invalid_argument`. Bands are not dropped silently.
  - `order ≥ 1`, plus the rules of `octave_bands`.
  - If no band qualifies, the result is empty.

## Consequences

- **The transient is included.** Levels from short inputs include the transient.
- **Vectors come from an independent float implementation.** The generator designs each
  band-pass from the analog poles (conventions: band Butterworth), then runs a direct-form-I
  cascade in plain Python floats. The tolerance is relative `1e-9`, for a recursive filter
  that is not bit-identical. The cases are:
  - thirds and octaves at 8 kHz;
  - order 2;
  - complex samples;
  - an empty band range;
  - the errors.
- **The tests check the physics.** A long tone at a band's center gives about `A²/2` in that band.
  For white noise, the band powers of contiguous bands sum to about the noise power inside
  them.
