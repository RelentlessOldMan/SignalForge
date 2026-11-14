# ADR 0079: Thomson's adaptive weights for the multitaper PSD

Status: accepted, 2026-11-13

## Context

The plain multitaper PSD (ADR 0078) averages the `K` eigenspectra with equal weight. The higher
tapers keep less of their energy inside `[−W, W]` (at NW 4 the seventh keeps about 94%), so where
the spectrum is far below its peak their leakage dominates: a tone at NW 4 with all seven tapers
leaks 3.6e-3 of its peak 6 bins away, about the rectangular window's level. Thomson (1982) weights
each eigenspectrum at each frequency by how much of it is signal rather than leakage, using the
estimate itself, and iterates to a fixed point.

## Decision

- `multitaper_psd(..., adaptive=False)` (C# `adaptive: false`). With `adaptive=True`, each
  two-sided FFT-order bin iterates `S' = Σ w_j S_j / Σ w_j`,
  `w_j = λ_j / (λ_j S + (1 − λ_j) σ²/fs)²`, from `S = (S_0 + S_1)/2`, where `S_j = |X_j|²/fs` are
  the eigenspectra, `λ_j` the concentrations and `σ² = Σ|x|²/N` the mean power. This is Thomson's
  `d_j = √λ_j S / (λ_j S + (1 − λ_j) σ²/fs)` with the common factor `S` removed from the weights,
  so that no bin divides 0 by 0.
- Each bin stops on its own when `|S' − S| ≤ 1e-10 S'`, or after 1000 repeats. A per-bin rule,
  not a whole-array one, keeps one bin's result from depending on another's convergence, so the
  two languages agree to about the stopping tolerance even if rounding moves one stop by a step.
- A bin whose estimate is exactly 0 stays 0; all-zero input gives zeros. Folding to one side, the
  frequency axis and the other result fields are as for the plain estimate.
- Measured on a tone at N 1024, NW 4, seven tapers: leakage 6 bins away falls from 3.6e-3 of the
  peak to 5.8e-7, and 50 bins away from 4.2e-5 to 2.9e-12. White noise stays at its level (1.003
  of it over 4096 samples). A pure tone takes about 130 repeats in its deep sidelobes; noise
  about 20.

## Not now

The F-test for line components and the degrees of freedom `2(Σ d_j²)² / Σ d_j⁴` per bin: a later
ADR, if wanted.

## Consequences

Expected values come from a stdlib generator that iterates the definition with its own tapers
(cyclic Jacobi, as for ADR 0078), plus two by-hand cases: one taper gives the plain estimate, and
equal eigenspectra give that common value whatever the weights.
