# ADR 0164: Frequency weightings A and C

Status: accepted, 2026-11-16. It sits beside the auditory scales in `units` (ADR 0154, 0160,
0163).

## Context

Sound level meters weight the spectrum with the A and C curves of IEC 61672-1. The standard
gives them analytically, from four pole frequencies:

- `f1 ≈ 20.598997` Hz;
- `f2 ≈ 107.65265` Hz;
- `f3 ≈ 737.86223` Hz;
- `f4 ≈ 12194.217` Hz.

It normalizes the curves to 0 dB at 1 kHz with the rounded constants `A1000 = −2.000` dB and
`C1000 = −0.062` dB. Implementations differ on two points:

- whether they subtract the rounded constants or the exact value at 1 kHz;
- whether they give the curve in dB or the filter itself.

## Decision

- **The scope.** The curve's value in dB at a frequency. A weighting filter (the bilinear
  transform of the analog poles) is a later item.
- **The formulas.** These use the four pole frequencies to the digits given above.
  - `A_raw(f) = 20·log10(f4²·f⁴ / ((f² + f1²)·√((f² + f2²)(f² + f3²))·(f² + f4²)))`.
  - `C_raw(f) = 20·log10(f4²·f² / ((f² + f1²)(f² + f4²)))`.
  - Each curve is its raw value minus the raw value at 1000 Hz, computed in the same way, so
    the result at 1 kHz is exactly 0 dB. The rounded constants differ from the exact ones by
    less than 0.0005 dB.
- **The API.** In `units`:
  - Python: `a_weighting(frequency)` and `c_weighting(frequency)`, which take scalars or
    arrays and return dB.
  - C#: `Units.AWeighting(frequency)` and `Units.CWeighting(frequency)`.
- **The edge.** `f = 0` gives `−inf`.
- **The rules.** Frequencies must be finite and `≥ 0`. Anything else is `invalid_argument`.
- **The arithmetic.** The code works in logs, with `log10(hypot(f, f_k))` for each
  `log10(f² + f_k²)/2`, so large frequencies do not overflow.

## Consequences

- **The vectors come from the closed form.** They are computed in 50-digit `decimal`. The
  generator also asserts two independent checks:
  - the standard's rounded `A1000` and `C1000`;
  - the standard's nominal design values at the base-10 frequencies `1000·10^(k/10)`, to their
    0.1 dB rounding.
