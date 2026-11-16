# ADR 0141: Odd-to-even harmonic ratio

Status: accepted, 2026-11-16. It builds on the harmonic series (ADR 0139).

## Context

A symmetric distortion, such as a clipped sine or a square wave, adds odd harmonics only. An
asymmetric one adds even harmonics as well. The odd-to-even ratio used in timbre descriptors is
the power in the odd harmonics over the power in the even ones. Definitions differ on two
points:

- whether the fundamental counts as odd. The common one counts it.
- whether the result is a ratio or in dB.

## Decision

- **The API.**
  - Python: `odd_even_ratio(heights, orders) -> float`.
  - C#: `Spectral.OddEvenRatio(heights, orders)`, where `orders` is a span of `int`.
  - `heights` are tone powers, such as PSD heights from `find_tones`. `orders` come from
    `harmonic_series`.
- **The value.**
  - The ratio is `Σ h_i` over odd orders (1, 3, 5, …) divided by `Σ h_i` over even orders
    (2, 4, …). The fundamental counts as odd.
  - Order 0 (unmatched) is left out.
  - It is a plain power ratio, not in dB.
- **Edge cases.**
  - Even power 0 with odd power above 0 gives `+inf`, as the spectral contrast and band energy
    ratio do (ADRs 0133, 0134).
  - Both sums 0 is `invalid_argument`.
- **The rules.**
  - The two arrays are 1-D and the same length.
  - `heights` are finite and `≥ 0`.
  - `orders` are whole numbers `≥ 0`. Python also accepts whole-valued floats.
  - Anything else is `invalid_argument`.

## Consequences

- **Reading the value.** A square wave gives `+inf`. A sawtooth, with every harmonic, gives a
  finite value above 1.
- **Vectors.** These are worked by hand in Fractions:
  - mixed orders.
  - orders in any sequence.
  - an unmatched tone that is left out.
  - odd harmonics only, giving `inf`.
  - even harmonics only, giving 0.
  - the errors.
- **Tests.**
  - Scaling the heights leaves the ratio unchanged.
  - Permuting the tones leaves it unchanged.
  - Clipping a sine symmetrically through `find_tones` and `harmonic_series` gives odd orders
    only, so the ratio is `inf`.
