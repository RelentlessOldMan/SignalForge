# 0016: Band-pass and band-stop Butterworth

Date: 2026-11-13. Status: accepted.

## Context

ADR 0014 designed Butterworth low-pass and high-pass filters and left band designs for later. A
band design doubles the order, and its poles no longer come in the simple pairs of the low-pass;
how they are grouped into sections, how the sections are ordered and how each is scaled must be
fixed for two implementations to produce the same rows.

## Decision

- **Transform the analog low-pass prototype**, then the bilinear transform with both edges
  prewarped (`L = tan(π·low/fs)`, `H = tan(π·high/fs)`; center `W = √(LH)`, width `B = H − L`).
  `order` is the prototype's order, as in the usual tools, so the filter has order `2·order` and
  `order` sections, and the −3 dB points are exactly the two edges.
- **One section per conjugate pair of band poles**: each prototype pole maps to two band poles
  (the roots of a quadratic), each with its conjugate from the conjugate prototype pole. The real
  prototype pole of an odd order maps to one quadratic, kept as one section whether its roots are
  complex or real.
- **Order**: the real pole's section first, then the prototype's pole pairs in order of rising Q
  as in ADR 0014, and within a pair the image with the smaller `|s|` (the lower one) first. The
  two images never have equal `|s|` in exact arithmetic (their product is `W²` and their sum is
  not real); in floating point they can tie for a band about `10⁻¹⁵·W` wide, and then the two
  sections are equal to rounding, so either order gives the same rows.
- **Scale from the analog factors**: a band-pass section is `B·s/(…)` and a band-stop section
  `(s² + W²)/(…)`; their product is exactly the transformed prototype, so the cascade has unit gain
  at the center (band-pass) or at DC and `fs/2` (band-stop) without a separate gain step. Single
  sections are not normalized: no one reference frequency suits every section of a band filter.
- Implemented from the definitions; no third-party code.

## Consequences

- The magnitude has a closed form in `tan(πf/fs)`, which the generator checks every band design
  against before writing it, and both test suites check across the band.
- A very narrow band gives high-Q sections whose individual gains can be well above 1 before the
  next section brings them back; this is normal for the form and not checked.
- Poles within about `10⁻⁸` of `z = 1` (an edge very near 0 Hz, or a band only a few `10⁻⁹·fs`
  wide) lose accuracy to rounding in the stored `[b, a]` rows: `butterworth_bandstop(4, 1e-8,
  0.2, 1)` has a DC gain of 1.03, not 1. Both languages give the same rows; the closed form holds
  only to that rounding. A second-order-section form cannot do better without another
  parameterization.
- The generator also checks each design independently of the pole-by-pole algorithm: every
  section is stable, and the product of the denominators equals the analog prototype's
  denominator expanded by polynomial substitution and the bilinear transform.
