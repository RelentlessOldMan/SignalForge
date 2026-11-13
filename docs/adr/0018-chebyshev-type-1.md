# 0018: Chebyshev type I IIR design

Date: 2026-11-13. Status: accepted.

## Context

A Butterworth filter (ADR 0014) is maximally flat but needs a high order for a sharp edge. A
Chebyshev type I filter trades a ripple in the pass band for a steeper transition at the same
order. Choices to fix: what the cutoff means, how the gain is set given the ripple, and the order
and scale of the sections.

## Decision

- **Low-pass and high-pass**, `chebyshev1_lowpass(order, ripple_db, cutoff, sample_rate)` and
  `chebyshev1_highpass(...)`, by the prewarped bilinear transform as for Butterworth, so the
  magnitude has the closed form `1/(1 + ε²·T_N(t/K)²)`.
- **The cutoff is the pass-band edge**, where the response last touches `−ripple_db`, the usual
  definition for this family; it is not the −3 dB point (that only coincides when the ripple is
  3.01 dB).
- **The ripple is in dB of power**, `ε² = 10^(R/10) − 1`, and must be positive.
- **Same sections as Butterworth**: the same order (real pole first, then rising Q), zeros and
  per-section unit gain at DC or `fs/2`, so the code shares one cascade builder with only the
  prototype poles different. An even order's response at DC (`fs/2` for the high-pass) is the
  ripple's low point, `10^(−R/20)`; that factor goes on the first section. The alternative,
  spreading it over the sections, makes no difference to the product and is harder to state.
- Implemented from the definitions; no third-party code.

## Consequences

- The generator computes the rows by another route (each analog pole pair's real quadratic through
  the bilinear transform) and checks every design against the closed form and against section
  stability before writing it; a stable cascade with the given zeros and that magnitude is unique
  up to how the poles are split, which the section order fixes.
- A cutoff within about `10⁻⁴·fs` of `fs/2` puts high-Q poles next to `z = −1`, and the stored
  rows then meet the closed form only to about `10⁻⁸` relative (a cutoff at `0.4999·fs`, order
  6 or more); both languages give the same rows. Tests check the closed form to `10⁻⁹` up to
  `0.49·fs`.
- Band-pass and band-stop Chebyshev, type II and elliptic designs are later work.
