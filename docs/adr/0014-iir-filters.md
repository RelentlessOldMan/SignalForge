# 0014: IIR filters as second-order sections

Date: 2026-11-13. Status: accepted.

## Context

FIR filters (ADR 0010) need many taps for a sharp edge; a receiver's channel filter or a DC block
is usually IIR. Choices to fix now: how a filter's coefficients are held, which designs come
first, how the sections of a design are ordered and scaled, and how the streaming filter relates
to the FIR one.

## Decision

- **Second-order sections only.** A filter is a cascade of rows `[b0, b1, b2, a0, a1, a2]`, never
  one long transfer function: a high-order polynomial loses precision in its roots, a cascade of
  biquads doesn't. The row layout is the one other tools use, so users can bring coefficients
  across. Python: a `(sections, 6)` array. C#: `double[][]`, like the spectrogram (ADR 0013),
  because it maps one to one onto JSON and the Python rows; a dedicated section type can come later
  without breaking it. Rows are divided by `a0` on the way in.
- **Butterworth first**, low-pass and high-pass, by the bilinear transform with the cutoff
  prewarped, so the −3 dB point is exactly at the cutoff and the magnitude has a closed form
  (`1/(1 + (tan(πf/fs)/tan(πf_c/fs))^(2N))`) that tests can check designs against.
- **Fixed section order and gain**, so two implementations produce the same rows: the real pole's
  first-order section first for odd orders, then pole pairs in order of rising Q; each section has
  unit gain at DC (low-pass) or `fs/2` (high-pass), which keeps every intermediate signal at about
  the input's level.
- **Streaming filter shaped like `FirFilter`**: `IirFilter(sos)` with `process`, `reset` and the
  same real-or-complex rule. The difference equation is the contract; the arithmetic form inside
  (transposed direct form II in both languages today) is not.
- Implemented from the definitions; no third-party code.

## Consequences

- Vectors fix the rows of each design, so a design change is a visible vector change. The
  generator computes them by a different route (the real biquad formulas from each pole pair's Q)
  from the library (mapping each complex pole through the bilinear transform).
- The Python filter runs a per-sample loop, slower than NumPy-vectorized code; fine for the sizes
  tests and measurements use today, revisit if profiling says so.
- Band-pass and band-stop Butterworth (done: ADR 0016), Chebyshev and elliptic designs, zero-phase (forward-backward)
  filtering (done: ADR 0017) and setting the initial state are later work.
