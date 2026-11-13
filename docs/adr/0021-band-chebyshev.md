# 0021: Band-pass and band-stop Chebyshev

Date: 2026-11-13. Status: accepted.

## Context

ADR 0016 transformed the Butterworth prototype to a band, and ADRs 0018 and 0020 gave the type I
and type II low-pass prototypes. A Chebyshev band design needs the same transform, but its
prototype poles are not on the unit circle, so the per-section gains of ADR 0016 (all 1, because
`|p_k| = 1`) no longer give the prototype's gain; and type II adds zeros, each of which maps to
two band zeros that must each be given to one section.

## Decision

- **Same transform, same section order** as ADR 0016: the odd order's real-pole section first,
  then each pole pair's two images in order of rising Q, the smaller `|s|` first. The real pole's
  quadratic `s² − c·s + W²` is kept as one section whether its roots are complex or real.
- **Gains come from the prototype's factors**, split evenly: the band-pass section of a pole pair
  gets `|p_k|` (type I) or `|p_k|/Ω_k` (type II), the square root of the pair's low-pass constant;
  the real-pole section gets `−p_r`. In the band-stop every constant is exactly 1 (the band-stop
  substitution turns `−p/(s_lp − p)` into `(s² + W²)/(s² − (B/p)s + W²)`), so no gain is applied.
  Type I of even order puts its `10^(−R/20)` on the first section, as the low-pass does. Butterworth
  is the case `|p_k| = 1`, so ADR 0016's rows are unchanged.
- **Type II zeros**: the prototype zero `jΩ` maps to two imaginary band zeros `jω_hi`, `jω_lo`
  with `ω_hi·ω_lo = W²`; `ω_lo` is computed as `W²/ω_hi` (the other root of the quadratic loses
  digits by cancellation). The section of the smaller-`|s|` pole takes `ω_lo`, the other `ω_hi`,
  which pairs each pole with the zero on its side of the band.
- **Edges**: `low` and `high` are where the transformed prototype frequency is 1: pass-band edges
  for type I, stop-band edges for type II, as for the low-pass and high-pass.
- Implemented from the definitions; no third-party code.

## Consequences

- The magnitude has a closed form in `tan(πf/fs)` for all four designs, which the generator and
  both test suites check.
- The band Butterworth becomes the shared band builder with the prototype passed in; its rows are
  unchanged.
- The generator builds the expected rows by the same pole-pair construction (as for ADR 0016);
  the independent checks are the closed-form magnitude and the denominator product.
