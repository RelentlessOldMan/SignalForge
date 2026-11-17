# ADR 0211: Lattice analysis filter

Status: accepted, 2026-11-17. It filters with the reflection coefficients of ADR 0210 directly.

## Context

The prediction-error filter can run as an FIR lattice. A lattice is driven by the reflection
coefficients, is modular in the order, and tolerates quantization of `k` well. It is the
analysis half of lattice speech coders.

## Decision

- **The API.**
  - Python: `lattice_filter(samples, reflection)` in `dsp`.
  - C#: `Dsp.LatticeFilter`, with real and complex overloads.
  - Both return `N` samples, the same length as the input. The output is complex if either
    input is complex.
- **The recursion.** It runs from zero state, with `b_{m−1}[−1] = 0`:
  - `f_0 = b_0 = x`;
  - for `m = 1 … p`:
    - `f_m[n] = f_{m−1}[n] + k_m·b_{m−1}[n−1]`;
    - `b_m[n] = b_{m−1}[n−1] + conj k_m·f_{m−1}[n]`.
  - The output is `f_p`, which equals `x` convolved with `reflection_to_lpc(k)` and cut to `N`
    samples. Any finite `k` is allowed, since the lattice needs no `|k| < 1`.
- **The rules.** Both inputs must be finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from a stdlib transcription of the recursion.
  - Each case is cross-checked in the generator against the direct-form convolution with the
    hand-expanded filter.
