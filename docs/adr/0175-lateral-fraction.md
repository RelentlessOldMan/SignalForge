# ADR 0175: Lateral energy fraction

Status: accepted, 2026-11-16. It goes with the ISO 3382 parameters in ADRs 0171 to 0174.

## Context

ISO 3382-1 measures apparent source width with the early lateral energy fraction:

    LF = Σ_{5 ms ≤ t < 80 ms} h_8² / Σ_{0 ≤ t < 80 ms} h_o²

Here `h_8` comes from a figure-of-eight microphone with its null towards the source, and `h_o`
from an omnidirectional one at the same point. Implementations differ on four points:

- how the window bounds round to samples;
- whether the bounds can be changed;
- the length rule;
- whether a result above 1 is clamped.

## Decision

- **The API.** In `measurements`, for real responses:
  - Python: `lateral_fraction(omni, figure_eight, sample_rate, *, start=0.005, stop=0.08)`.
  - C#: `Measurements.LateralFraction(omni, figureEight, sampleRate, start = 0.005,
    stop = 0.08)`.
- **The bounds.** `N_a = ⌊start·fs + 1/2⌋` and `N_b = ⌊stop·fs + 1/2⌋`, the rounding of
  ADR 0172.
  - The numerator is `Σ_{N_a ≤ n < N_b} h_8[n]²`.
  - The denominator is `Σ_{n < N_b} h_o[n]²`.
  - Both sums are clipped to the length.
  - Both responses start at index 0, which is the direct sound, as in ADR 0172.
- **No clamping.** The two microphones are calibrated separately, so LF can exceed 1, and it is
  returned as computed.
- **The rules.**
  - The responses are one-dimensional, real, finite, and of equal non-zero length.
  - `sample_rate` is finite and positive.
  - `0 ≤ start < stop`, both finite, and `N_b ≥ 1`.
  - The omni energy below `N_b` is not zero.
  - Anything else is `invalid_argument`.
  - `N_a = N_b` is allowed, and gives 0.

## Consequences

- **Vectors are exact sums.** They are hand sums in fractions, plus the geometric window sums
  `(q^a − q^b)/(1 − q)` in 50-digit `decimal`. One case gives a result above 1, and another
  has a window past the end.
