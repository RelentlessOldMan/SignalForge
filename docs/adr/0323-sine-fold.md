# ADR 0323: Sine wavefolder

Status: accepted, 2026-11-18.

## Context

The triangle wavefolder (ADR 0252) reflects the signal at sharp corners, and every corner
adds a spray of high harmonics. Reading the input through a sine instead folds it smoothly:
`sin((π/2)·g·x)`. A full-scale input at `g = 1` maps onto one rising quarter-cycle, and each
step of 2 in `g` adds a fold. The harmonics fall off much faster than the triangle folder's,
which is the soft, rounded West Coast folding sound.

## Decision

- **The API.**
  - Python: `sine_fold(samples, drive)` in `dsp`.
  - C#: `Dsp.SineFold(ReadOnlySpan<double> samples, double drive)`.
  - Real output, one per sample.
- **The value.**
  - `k = (π/2)·drive`, computed once.
  - `y = sin(k·x)`.
  - The output is odd in `x` and stays in `[−1, 1]`. At `drive ≤ 1`, an input within `[−1, 1]`
    is not folded.
- **The rules.**
  - `samples` real, one-dimensional, non-empty and finite.
  - `drive` finite and positive.

## Consequences

- **Vectors.**
  - The generator computes `k` and `math.sin(k·x)`.
  - Cases at `k·x = π/2` and `π` check the peak and the first fold exactly, to a rounding of
    `π`.
  - The tolerance is `abs 1e-12, rel 1e-12`.
