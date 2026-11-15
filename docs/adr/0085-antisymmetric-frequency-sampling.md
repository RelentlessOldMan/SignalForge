# ADR 0085: Antisymmetric frequency sampling

Status: accepted, 2026-11-14

## Context

Frequency sampling ([ADR 0084](0084-frequency-sampling-fir.md)) makes symmetric taps only. Hilbert
transformers and differentiators need antisymmetric taps (types III and IV). Equiripple design
already has them, as `kind` ([ADR 0026](0026-antisymmetric-equiripple.md)), with an amplitude
convention: `H = −j·e^(−j2πfc/fs)·A`. A second design should not define the same idea
differently.

## Decision

- **`kind` on `fir_frequency_sampling`**: `"filter"` (the default), `"hilbert"` or
  `"differentiator"`, with equiripple design's meanings.
  - `"hilbert"`: the amplitude target is the gain.
  - `"differentiator"`: the target is `−2πν·gain`, so a gain of 1 is the derivative per sample.
- **C#**: `EquirippleKind` is renamed `FirKind` and shared by both designs. Nothing is published
  yet, so the rename costs no users. Two enums with the same three values would be worse.
- **The taps**: the grid samples are `−j·e^(−iπk(N−1)/L)·A_k`, and their Hermitian inverse DFT is
  the sine sum `d(t) = (1/L)[2 Σ_{k=1}^{K−2} A_k sin(2πkt/L) + A_{K−1} sin(πt)]`. The windowed taps
  are then made exactly antisymmetric, `h ← (h − reversed h)/2`, so an odd-length design's centre
  tap is exactly 0.
- **Targets that cannot be met raise**, as an even-length filter's nonzero fs/2 gain already does:
  - every antisymmetric design has `A(0) = 0`, so `"hilbert"` needs gain 0 at 0;
  - type III (odd `N`) has `A(fs/2) = 0`, so both kinds need gain 0 at fs/2.
  - The differentiator's `A(0)` is 0 by construction, so it has no condition at 0.
- **Antisymmetric kinds need `num_taps ≥ 2`**, as in equiripple design.
- **Expected values**: the frequency-sampling generator's direct sine sums, and by-hand cases:
  - the 3-tap differentiator `[π/4, 0, −π/4]` (`K = 3`, rectangular window);
  - the 2-tap Hilbert `[−(2+√2)/8, (2+√2)/8]`;
  - the 2-tap differentiator `[π(2+√2)/8, −π(2+√2)/8]`.

## Consequences

- A C# caller of `FirEquiripple` that names `EquirippleKind` must write `FirKind`.
