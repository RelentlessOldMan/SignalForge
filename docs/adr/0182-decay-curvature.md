# ADR 0182: Decay curvature

Status: accepted, 2026-11-16. It goes with the reverberation time of ADR 0171.

## Context

ISO 3382-2 Annex B checks whether a decay is straight by comparing two fits over different
ranges. The curvature is `C = 100·(T30/T20 − 1)` percent:

- T20 is the fit from −5 to −25 dB;
- T30 is the fit from −5 to −35 dB.

A single exponential gives 0. A decay that bends towards a slower tail gives a positive value,
and values above about 10 % mark a decay that is not a single slope.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `decay_curvature(impulse_response, sample_rate)`.
  - C#: `Measurements.DecayCurvature(impulseResponse, sampleRate)`.
- **What it is.** It is exactly `100·(T30/T20 − 1)`, from the two `reverberation_time` fits of
  ADR 0171. It uses the same Schroeder decay, the same threshold samples and the same errors.
  The decay must therefore reach −35 dB with at least two samples in each range.
- **The result.** It is in percent and signed, with no clipping.

## Consequences

- **Vectors.** Expected values come from the exact geometric Schroeder tails of sums of
  `c·rⁿ`, with both least-squares slopes worked in 50-digit `decimal`. The cases are:
  - a single exponential, which gives close to 0;
  - a sum of two decays, which gives a positive value;
  - complex input.

  Every curve value is kept at least `1e−6` dB away from −5, −25 and −35 dB.
