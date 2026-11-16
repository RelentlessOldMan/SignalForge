# ADR 0145: Harmonic centroid and spread

Status: accepted, 2026-11-16. It builds on the harmonic series (ADR 0139) and the harmonic
deviation (ADR 0144).

## Context

The harmonic spectral centroid is the weighted mean frequency of a sound's harmonics. The
harmonic spread is their weighted standard deviation about it. Unlike the spectral centroid
(ADR 0121), they ignore the noise between the harmonics. Definitions differ on
three points:

- the weights, which may be amplitudes or powers;
- the frequencies, which may be the measured tones or `m·f0`;
- whether the spread is normalized by the centroid.

## Decision

- **The API.**
  - Python: `harmonic_centroid(frequencies, heights, orders)`, returning
    `HarmonicCentroid(centroid, spread)`.
  - C#: `Spectral.HarmonicCentroid(frequencies, heights, orders)`, returning the record
    `HarmonicCentroid(Centroid, Spread)`, where `orders` is a span of `int`.
- **The weights.** Each tone's weight is its amplitude `a_i = sqrt(h_i)`, as in the tristimulus
  and the harmonic deviation.
- **The tones.** Each tone with order `≥ 1` counts once, at its measured frequency `t_i`, so a
  detuned partial moves the centroid. Order 0 is left out.
- **The value.**
  - `centroid = Σ a_i t_i / Σ a_i`, in Hz.
  - `spread = sqrt(Σ a_i (t_i − centroid)² / Σ a_i)`, in Hz, not normalized.
- **The rules.**
  - The three arrays are 1-D and the same length.
  - Frequencies are finite and positive, and heights are finite and `≥ 0`.
  - Orders are whole numbers `≥ 0`. Python also accepts whole-valued floats.
  - The matched amplitudes sum to more than 0.
  - Anything else is `invalid_argument`.

## Consequences

- **The relative spread.** Callers who want it divide `spread` by `centroid`.
- **Vectors.** These are worked by hand in Fractions, with perfect-square heights. The spread
  is the square root of an exact fraction.
  - a falling series.
  - equal weights.
  - a single tone, whose spread is 0.
  - an unmatched tone.
  - a zero-height tone.
  - the errors.
- **Tests.**
  - Scaling the heights leaves both values unchanged.
  - Scaling the frequencies scales both.
