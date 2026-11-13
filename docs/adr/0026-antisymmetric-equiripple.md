# ADR 0026: Hilbert transformers and differentiators by equiripple design

Status: accepted, 2026-11-13

## Context

`fir_equiripple` designs symmetric taps (types I and II). Hilbert transformers and
differentiators need antisymmetric taps (types III and IV), whose response is imaginary times a
delay. The same exchange solves them once the amplitude is factored as `A = Q·P` with
`Q = sin(2πν)` or `sin(πν)`. Choices other libraries make differently: how the kind is named, the
sign of `A`, what `desired` means for a differentiator, and how its error is weighted.

## Decision

- **A `kind` argument on `fir_equiripple`**: `"filter"` (default), `"hilbert"`,
  `"differentiator"`; in C# the enum `EquirippleKind`. One function, since the grid, exchange,
  start and checks are shared; the parity of `num_taps` still picks the type within a kind.
- **The sign of `A` makes `desired` 1 the ideal**: `H = −j·delay·A`, so a Hilbert transformer with
  `desired` 1 has `H = −j` at positive frequencies (the analytic-signal convention, `cos → sin`).
  A differentiator's `desired` is the slope of `H/(j·delay)` per radian per sample: `desired` 1
  approximates `d/dn`, the derivative per sample (multiply by `fs` for per second). Its target is
  then `T = −2πν·D` in terms of `A`; the minus sign stays inside the convention.
- **A differentiator's error is relative where `desired ≠ 0`**: weight `W_j/(2πν)`, so the error
  is in the slope's units and a low-frequency band is not left with a large relative error. Bands
  with `desired` 0 (a stopband above the differentiating band) keep the plain weight.
- **Where `Q = 0` the target must be 0**, else `invalid_argument`, as type II already did at
  `fs/2`: a Hilbert band from 0, or a type III band to `fs/2` with a nonzero target, cannot be
  met and silently dropping the point would hide that. A differentiator's target at 0 is 0, so a
  band from 0 is allowed; the point is dropped.
- Expected values: small designs by hand, and the 50-digit generator extended to types III and IV
  (sine factor `Q`, its own conversion to taps), certified by alternation as before.

## Consequences

- Existing calls are unchanged; `S` in the stopping and tap checks is now the largest `|W·T|` on
  the grid, which equals the old `max_j |W_j·D_j|` for filters.
- `num_taps = 1` is invalid for the antisymmetric kinds (no free tap).
