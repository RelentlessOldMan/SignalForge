# ADR 0086: Antisymmetric least-squares design

Status: accepted, 2026-11-14

## Context

Equiripple ([ADR 0026](0026-antisymmetric-equiripple.md)) and frequency-sampling
([ADR 0085](0085-antisymmetric-frequency-sampling.md)) design both make Hilbert transformers and
differentiators through `kind`. Least-squares design ([ADR 0029](0029-least-squares-fir.md)) made
symmetric taps only. Its error is an exact integral, so the antisymmetric kinds need closed-form
integrals of sine bases.

## Decision

- **`kind` on `fir_least_squares`**: `"filter"` (the default), `"hilbert"` or `"differentiator"`.
  The taps, the offsets and the amplitude `A` are as for equiripple design:
  `H = −j·e^(−j2πfc/fs)·A`, `A(ν) = Σ_m 2·h[c + m]·sin(2πmν)`.
- **The target**: `"hilbert"` fits `A` to the band's linear gain `D_j(ν)`. `"differentiator"` fits
  `A` to `−2πν·D_j(ν)`, so a gain of 1 is the derivative per sample.
- **The weight is plain `W_j`, also for the differentiator.** Equiripple design weights a
  differentiator's error by `1/(2πν)`, making it relative to the slope. Here that would put
  `sin·sin/ν²` under the integral, which has no elementary closed form. An exact integral is the
  point of this design, so least squares keeps the absolute error. A user who wants the error
  smaller at low frequencies can split the band and weight the low part more.
- **Targets the type cannot meet are part of the error, not an error.** Every antisymmetric design
  has `A(0) = 0`, and type III (odd `N`) also has `A(fs/2) = 0`. A nonzero `desired` there is
  fitted as closely as the type allows. Even-length filters already work that way at fs/2 in this
  design. Frequency sampling raises instead, because it samples the target exactly at 0 and fs/2,
  so a silently dropped sample there would change the taps unseen.
- **Antisymmetric kinds need `2 ≤ num_taps ≤ 1001`.**
- **The normal equations** use `(C(t_k − t_l) − C(t_k + t_l))/2` for `∫ sin·sin`, and the sine
  moments `∫ ν^i sin(2πuν) dν` for `i = 0, 1, 2` (the differentiator's target is quadratic in `ν`).
  No offset is 0, so the moments have no special case.
- **Expected values**: the least-squares generator, extended with the sine moments, checked
  against Simpson quadrature and solved exactly in rational arithmetic. By-hand cases:
  - the 2-tap Hilbert over `[0, fs/2]` with gain 1: `[−2/π, 2/π]`;
  - the 3-tap differentiator over `[0, fs/2]` with gain 1: `[1, 0, −1]`.

## Consequences

- All three FIR designs that take a band target now share `kind`.
- A least-squares differentiator and an equiripple one with the same arguments differ by more
  than the error measure, because their weights differ at low frequencies.
