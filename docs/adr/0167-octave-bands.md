# ADR 0167: Fractional-octave bands

Status: accepted, 2026-11-16. It sits beside the frequency weightings (ADR 0164), for
octave-band analysis.

## Context

IEC 61260-1 defines fractional-octave bands, with `b` bands per octave, around a reference of
1000 Hz:

- The octave ratio is `G = 10^(3/10)` (base 10), not 2.
- The exact mid-band frequencies are:
  - `f_m = 1000·G^(x/b)` for odd `b`;
  - `f_m = 1000·G^((2x + 1)/(2b))` for even `b`;
  - for every integer `x`.
- The band edges are `f_m·G^(∓1/(2b))`.
- The familiar labels (31.5, 63, 125 …) are rounded nominal names, not the frequencies
  themselves.

Implementations differ on three points:

- base 10 or base 2;
- exact or nominal frequencies;
- which bands a range includes.

## Decision

- **The API.** In `units`:
  - Python: `octave_bands(fraction, min_frequency, max_frequency)`, returning an array of
    shape `(bands, 3)`.
  - C#: `Units.OctaveBands(fraction, minFrequency, maxFrequency)`, returning `double[][]`.
  - Each row is `[lower, center, upper]` in Hz, in ascending order.
- **The frequencies.** These follow the standard's exact base-10 formulas above, with
  `b = fraction`. There are no nominal values.
- **The range.** A band is included when its mid-band frequency `f_m` is in
  `[min_frequency, max_frequency]`, compared in floating point. The edges may extend past the
  range. If no band qualifies, the result is empty, with 0 rows.
- **The rules.**
  - `fraction ≥ 1` is an integer; any value is allowed, not only 1, 3, 6, 12 or 24.
  - `0 < min ≤ max`, both finite.
  - Anything else is `invalid_argument`.

## Consequences

- **Band boundaries are floating point.** A range limit within a few ulps of a mid-band
  frequency may include or exclude that band differently in the two languages. `1000` itself
  is exact (`G^0`). The vectors keep the limits away from mid-band frequencies.
- **Vectors come from the closed form.** They use powers of `10^(3/10)` in 50-digit
  `decimal`. The generator also asserts that the octave and third-octave mid-band frequencies
  lie within 1.5 % of the standard's nominal names. The cases are:
  - octaves over 20 Hz to 20 kHz;
  - thirds;
  - the even fractions 2 and 6;
  - a single band;
  - the errors.
