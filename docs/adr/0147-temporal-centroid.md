# ADR 0147: Temporal centroid

Status: accepted, 2026-11-16.

## Context

The temporal centroid is the time at which a signal's energy is centred. Its spread measures
how long the signal lasts. They are the time-domain twins of the spectral centroid and spread
(ADR 0121). Definitions differ on three points:

- the weights, which may be energy `|x|²`, amplitude `|x|`, or a smoothed envelope;
- the time origin;
- the unit, which may be seconds or samples.

## Decision

- **The API.**
  - Python: `temporal_centroid(samples, sample_rate)`, returning `TemporalCentroid(centroid,
    spread)`.
  - C#: `Measurements.TemporalCentroid(samples, sampleRate)`, for real and complex spans,
    returning the record `TemporalCentroid(Centroid, Spread)`.
- **The weights.** Each sample weighs its energy `p_n = |x[n]|²`, as for the spectral moments,
  which weigh power. No envelope smoothing is applied; callers smooth first if they want it.
- **The times.** Sample `n` is at `t_n = n / fs` seconds, so sample 0 is at `t = 0`.
- **The value.**
  - `centroid = Σ p_n t_n / Σ p_n`, in seconds.
  - `spread = sqrt(Σ p_n (t_n − centroid)² / Σ p_n)`, in seconds.
- **The rules.**
  - The samples are 1-D and finite, real or complex, with at least one of them.
  - `sample_rate` is finite and positive.
  - The samples' energy sums to more than 0.
  - Anything else is `invalid_argument`.

## Consequences

- **Samples.** Callers who want samples pass `sample_rate = 1`.
- **A delay.** Delaying the signal by `k` samples moves the centroid by `k / fs` and leaves the
  spread unchanged.
- **Vectors.** These are worked by hand in Fractions. The spread is the square root of an exact
  fraction.
  - an impulse, whose spread is 0.
  - a symmetric pulse.
  - a ramp.
  - a complex signal.
  - a sample rate other than 1.
  - the errors.
- **Tests.**
  - A delay shifts the centroid and leaves the spread unchanged.
  - Scaling the samples leaves both unchanged.
