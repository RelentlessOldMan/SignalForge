# ADR 0247: Uniform quantizer

Status: accepted, 2026-11-17.

## Context

ADC models, fixed-point studies and SQNR measurements need values rounded to a grid. They can
also need the grid to saturate at a full-scale level. Rounding at a tie is where two
implementations most often disagree, so this ADR fixes the tie rule.

## Decision

- **The API.**
  - Python: `quantize(samples, step, *, levels=None)` in `dsp`.
  - C#: `Dsp.Quantize(samples, step, levels = null)`, real or complex in, the same kind out.
  - Complex samples are quantized part by part.
- **The value.**
  - The quantizer is mid-tread: `k = round(x/step)`, then `y = step·k`.
  - `x/step` is one IEEE division. `round` rounds half to even: `np.rint` in Python and
    `Math.Round(·, MidpointRounding.ToEven)` in C#.
  - With `levels = L`, which must be odd, `k` is clamped to `[−(L − 1)/2, (L − 1)/2]` before the
    multiplication. `L = 1` gives all zeros.
- **The rules.**
  - `step` must be finite and `> 0`.
  - `levels` must be `None`, or an odd integer `≥ 1`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The steps are binary fractions and the samples are multiples of `step/4`. So `x/step` is exact,
    and the rounding is decided by hand.
  - The cases include ties, such as `0.5`, `1.5`, `−2.5` and `−0.5` steps, which round to even.
