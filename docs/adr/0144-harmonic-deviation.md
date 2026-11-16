# ADR 0144: Harmonic spectral deviation

Status: accepted, 2026-11-16. It builds on the harmonic series (ADR 0139) and the tristimulus
(ADR 0142).

## Context

Harmonic spectral deviation measures how jagged the harmonic amplitudes are. It compares each
harmonic's amplitude with a smooth envelope, usually the mean of the harmonic and its two
neighbours. Definitions differ on several points:

- the envelope at the first and last harmonic;
- missing orders;
- duplicate tones at one order;
- the normalization. Some leave the deviation in amplitude units, and some divide by the
  number of harmonics or by the total amplitude.

## Decision

- **The API.**
  - Python: `harmonic_deviation(heights, orders) -> float`.
  - C#: `Spectral.HarmonicDeviation(heights, orders)`, where `orders` is a span of `int`.
- **The amplitudes.**
  - Take `H` as the highest order. Then `a_m = sqrt(Σ h_i)` over the tones with order `m`, for
    `m = 1..H`, as in the tristimulus.
  - Duplicates add as powers.
  - A missing order has amplitude 0, since a gap in the series is a deep notch in its envelope.
  - Order 0 is left out.
- **The envelope.** `e_m` is the mean of `a_{m−1}`, `a_m` and `a_{m+1}`, taking only the
  neighbours inside `1..H`. So `e_1 = (a_1 + a_2)/2`, and with `H = 1`, `e_1 = a_1`.
- **The value.** `deviation = Σ_m |a_m − e_m| / Σ_m a_m`. It is dimensionless and does not
  change when the heights are scaled. 0 means a straight-line envelope.
- **The rules.**
  - The arrays are 1-D and the same length.
  - Heights are finite and `≥ 0`.
  - Orders are whole numbers `≥ 0`. Python also accepts whole-valued floats.
  - `Σ a > 0`.
  - Anything else is `invalid_argument`.

## Consequences

- **The cost.** Memory and time are linear in the highest order. Orders from `harmonic_series`
  are at most its `max_order`.
- **Vectors.** These are worked by hand in Fractions, from perfect-square heights:
  - a flat series.
  - a bowl.
  - a gap.
  - duplicate orders.
  - an unmatched tone.
  - a permuted series.
  - a single harmonic.
  - the errors.
- **Tests.**
  - Scaling the heights leaves the value unchanged.
  - A series falling linearly in amplitude deviates only at the two ends, and the value matches
    one computed directly.
