# ADR 0158: Delta coefficients

Status: accepted, 2026-11-16. It follows MFCC (ADR 0157).

## Context

Feature sequences such as MFCCs are usually extended with their slopes over time, the delta
coefficients. HTK defines them as a least-squares regression over `±W` frames. Implementations
differ on the edges:

- HTK repeats the first and last frames;
- librosa can interpolate, or pad in other ways;
- some implementations return a shorter sequence.

## Decision

- **The API.**
  - Python: `delta(frames, width=2)`, in `spectral`. It takes a 2-D array of `T` frames (rows)
    by `D` features and returns the same shape.
  - C#: `Spectral.Delta(double[][] frames, int width = 2)`, returning `double[][]` with one row
    per frame.
- **The formula.** Per column,
  `d_t = Σ_{n=1}^{W} n·(c_{t+n} − c_{t−n}) / (2·Σ_{n=1}^{W} n²)`.
- **The edges.** An index outside `0 … T−1` is clamped to the nearest frame, as HTK does. So
  the output has `T` rows, and a single frame gives all zeros.
- **Order.** It is applied once. Delta-deltas are `delta(delta(frames))`.
- **The rules.**
  - `frames` is 2-D with at least one row and one column, all rows the same length, all finite.
  - `width` is an integer of at least 1.
  - Anything else is `invalid_argument`.

## Consequences

- **A ramp gives its slope.** For `c_t = a·t + b`, `d_t = a` wherever `t ± W` stays inside the
  sequence. Near the edges, the clamped frames pull it down.
- **Vectors are exact.** They use `fractions.Fraction` from the formula with clamped indices:
  - a ramp with width 1 and width 2;
  - one frame;
  - a width larger than the sequence;
  - an alternating sequence;
  - the errors.
- **Tests.**
  - A ramp's interior slope.
  - A constant gives zeros.
  - Linearity.
