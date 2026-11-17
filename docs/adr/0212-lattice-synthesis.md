# ADR 0212: Lattice synthesis filter

Status: accepted, 2026-11-17. It is the inverse of ADR 0211.

## Context

A lattice coder resynthesizes speech from the excitation and the reflection coefficients
through the all-pole lattice. With `|k| < 1` this filter is stable, and the check is trivial.

## Decision

- **The API.**
  - Python: `lattice_synthesis(excitation, reflection)` in `dsp`.
  - C#: `Dsp.LatticeSynthesis`, with real and complex overloads.
  - Both return `N` samples. The output is complex if either input is complex.
- **The recursion.** For each sample `n`, from zero state:
  - start with `f_p[n] = e[n]`;
  - for `m = p … 1`:
    - `f_{m−1}[n] = f_m[n] − k_m·b_{m−1}[n−1]`;
    - `b_m[n] = b_{m−1}[n−1] + conj k_m·f_{m−1}[n]`;
  - then `y[n] = b_0[n] = f_0[n]`.
  - This is `1/A(z)` with `A = reflection_to_lpc(k)`, so
    `lattice_synthesis(lattice_filter(x, k), k) = x`.
- **The rules.** These are ADR 0211's: both inputs finite and non-empty, and any finite `k`.

## Consequences

- **Vectors.**
  - The expected values come from a stdlib transcription of the recursion.
  - The generator cross-checks each case against the direct all-pole recursion
    `y[n] = e[n] − Σ_{j≥1} a_j y[n−j]`, and checks that the analysis lattice gives `e` back.
