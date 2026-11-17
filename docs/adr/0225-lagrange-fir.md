# ADR 0225: Lagrange fractional-delay FIR

Status: accepted, 2026-11-17. It sits beside ADR 0040's windowed-sinc `fractional_delay`.

## Context

ADR 0040 delays a signal with a long windowed sinc, which is accurate across the band. Many
uses want a short filter instead: timing recovery, Farrow interpolators, sample-rate converters
and delay lines. For those, the Lagrange interpolator is the standard short FIR. It is exact for
polynomials up to its order and maximally flat at DC.

## Decision

- **The API.** Python: `lagrange_fir(delay, order)` in `dsp`. C#: `Dsp.LagrangeFir(delay, order)`.
  Both return `order + 1` real taps.
- **The value.**
  - `h[k] = Π_{m=0, m≠k}^{N} (D − m)/(k − m)` for `k = 0 … N`, with `N = order`.
  - The product is taken in order of increasing `m`.
  - `D` is measured from tap 0: `y[n] = Σ_k h[k]·x[n−k]` approximates `x[n − D]`.
  - For any polynomial `x` of degree `≤ N` the result is exact, so `Σ_k h[k]·k^q = D^q` for
    `q ≤ N`.
  - An integer `D` in `0 … N` gives the unit impulse at `D`.
  - Accuracy is best for `(N − 1)/2 ≤ D ≤ (N + 1)/2`. Other `D` are allowed and extrapolate.
- **The rules.** `delay` must be finite, and `order` an integer `≥ 1`.

## Consequences

- **Vectors.**
  - The expected values are exact fractions:
    - order 1 is `[1 − D, D]`;
    - order 2 at `D = 1/2` is `[3/8, 3/4, −1/8]`;
    - order 3 at `D = 3/2` is `[−1/16, 9/16, 9/16, −1/16]`.
  - The generator checks the moment identity `Σ h[k]·k^q = D^q` for each case.
- **Follow-ups.** ADR 0040's Farrow structure for time-varying delays can now be built from
  these polynomials.
