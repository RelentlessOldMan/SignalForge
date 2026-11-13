# 0024: Equiripple FIR design

Date: 2026-11-13. Status: accepted.

## Context

Windowed-sinc designs (ADR 0010) are simple but not optimal: for a given length, the
Parks–McClellan (Remez exchange) design has the smallest largest weighted error. Implementations
differ in their frequency grid, so their results differ slightly: the optimum depends on the set
of frequencies the error is measured on.

## Decision

- **`fir_equiripple(num_taps, bands, desired, sample_rate, weights=None, grid_density=16)`**:
  piecewise-constant desired gain per band, a positive weight per band, odd (type I) or even
  (type II) length. Differentiators and Hilbert transformers (antisymmetric taps) are not
  included.
- **The grid is part of the convention**, so the result is defined as the unique discrete
  optimum on it, independent of the algorithm: edges included exactly, points evenly spaced in
  each band at about `0.5/(grid_density·L)`.
- **Remez exchange with barycentric interpolation**, the weights from logarithms (the plain
  products overflow by about 1000 taps), and deterministic tie rules so both languages walk the
  same path. The stop rule is an unchanged extremal set, which on a finite grid is exact, or a
  largest error within 1e-9 relative (plus a rounding allowance) of `|δ|`, since optima with an
  extra ripple otherwise swap between two equally good sets forever.
- **Taps by a direct solve** at the final set, not by sampling the interpolant on a uniform
  frequency grid and inverting a DFT: the uniform samples fall in the transition gaps, where the
  interpolant magnifies rounding by many orders (a 41-tap design measured 2e-8 stopband error
  instead of its 3e-11 optimum that way). The taps are checked on the grid against `|δ|` with a
  0.1% margin: a first margin of 1e-6 rejected usable designs whose coefficients are large
  enough (wide gaps between bands) that rounding alone exceeds it, while the failures the check
  is for (a broken tap conversion, cancellation at the precision limit) miss by far more.
- **The old extremal set always counts in the exchange**, with its alternating signs: otherwise a
  first set lying only in bands whose desired value is 0 gives `δ = 0`, zero errors there, and
  too few extrema; and rounding at the set's last point (not an interpolation node) could flip a
  sign. A random sweep against the generator's 50-digit solver found both.
- **Limits**: `num_taps ≤ 1001`, `grid_density ≤ 64`, 250 iterations. Designs whose ripple is
  near or below 1e-13 lose `δ` to cancellation; they raise rather than return something
  wrong. The 1001 limit keeps the Python grid arrays to a few MB.
- Implemented from the published description of the algorithm; no third-party code.

## Consequences

- Expected values: small designs solved by hand, and a generator that solves the same discrete
  problem by a different route (linear solves in the cosine basis) and certifies each result by
  the alternation theorem (the error alternates `L + 1` times at `±δ` and is nowhere larger on
  the grid).
- Results differ from other libraries' Remez designs by the grid effect (about 1e-4 relative in
  the ripple for the default density), not by more.
