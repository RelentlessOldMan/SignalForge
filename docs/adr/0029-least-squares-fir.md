# ADR 0029: Least-squares FIR design

Status: accepted, 2026-11-13

## Context

Windowed sinc controls the transition only through the window; equiripple minimizes the largest
error. The least-squares design minimizes the error energy instead, which gives lower average
stopband error and allows a gain that varies linearly across a band. Choices other libraries make
differently: a grid or exact integrals, how `desired` describes a band, and which tap counts are
allowed.

## Decision

- **`fir_least_squares(num_taps, bands, desired, sample_rate, weights=None)`**, beside
  `fir_equiripple`, with the same band rules. `desired` holds **two values per band** (lower and
  upper edge, linear between), so `len(desired) == len(bands)`; this also describes
  differentiator-like slopes without a `kind`.
- **Exact integrals**: the normal equations' entries are closed-form integrals of cosines and of
  `ν·cos`, so the result does not depend on a grid density and the expected values have a
  definition both languages can reach independently.
- **Odd and even `num_taps`**: even is type II; its zero at `fs/2` is simply part of the error, no
  error is raised (unlike equiripple, where a nonzero target at a zero of `Q` cannot be levelled).
- **Solving**: the system is symmetric positive definite; the languages may solve it differently
  (LU with pivoting in NumPy, Gaussian elimination with partial pivoting in C#). Vectors use sizes
  whose `G` is well conditioned.
- Expected values: small designs by hand (orthogonal cosines over `[0, fs/2]`), and a stdlib
  generator that evaluates the same integrals, checks each against composite Simpson quadrature,
  and solves the system exactly in rational arithmetic.

## Consequences

- Narrow bands with long filters make `G` ill-conditioned; the taps are then determined only to
  rounding times its condition, as for any least-squares design.
