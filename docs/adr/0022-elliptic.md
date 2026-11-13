# 0022: Elliptic (Cauer) low-pass and high-pass

Date: 2026-11-13. Status: accepted.

## Context

The elliptic filter is the steepest of the classical designs for a given order: equiripple in the
pass band and the stop band. It needs the Jacobi elliptic functions and the complete elliptic
integral, which NumPy does not provide and the C# library cannot take a dependency for, so both
languages implement them. Several published methods give the poles and zeros; they differ in how
the selectivity `k` is found and in how the elliptic functions are evaluated, which changes the
last digits.

## Decision

- **API**: `elliptic_lowpass(order, ripple_db, attenuation_db, cutoff, sample_rate)` and
  `elliptic_highpass(...)` (`EllipticLowpass` and `EllipticHighpass`), with `cutoff` the pass-band
  edge, as for type I. The stop-band edge follows from the order and the two levels; a function
  to choose the order from both edges can come later.
- **Elliptic functions by the descending Landen transformation** (the method of the standard
  filter-design lecture notes): a short ladder of moduli, `K` as a product, `cd` by ascending
  recursion from a cosine, which works unchanged for complex arguments. The ladder carries each
  complement separately (`m' ← 2√m'/(1 + m')`), so moduli near 1 keep their digits.
- **Selectivity from the nome** with the q-product for `k` or `k'` (whichever is below `1/√2`),
  so neither a tiny `k₁` (high attenuation) nor a `k` near 1 (narrow transition) loses digits.
- **`v₀` in real arithmetic**: the inverse `sn` of `j/ε_p` stays on the imaginary axis through
  the Landen recursion, so it is computed as a real `asinh`, with no complex `asin` (whose
  accuracy varies between runtimes).
- **Sections reuse the type II builder**: pair `i` (`u_i = (2i + 1)/N`) has its poles and its own
  zeros; the Butterworth order and per-section unit gain, and type I's `10^(−R/20)` for an even
  order, so `|H(0)| = 1` (odd) or `10^(−R/20)` (even).
- `ripple_db < attenuation_db` is required; equal levels have no elliptic design.
- Implemented from the mathematical definitions; no third-party code.

## Consequences

- The generator computes the expected rows by a different route: theta-function series for `k`
  and `cd`, and the poles as the left-half-plane roots of `D(ω)² + ε_p²·N(ω)²` found
  numerically, then checks `R_N`'s defining equiripple property, the closed-form `|H|²` of the
  rows, and stability. Order 2 has a closed form (`R_2` is a ratio of quadratics), used as a
  by-hand vector.
- Designs with `k' < 1e-6` (very high orders, or close levels for the order) are rejected: their
  stop band would start within 5e-13 of the cutoff, and the poles round onto the unit circle
  (one language's pole check fired, the other's did not, at `k' ≈ 2e-11`).
