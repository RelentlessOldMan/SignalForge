# ADR 0259: Tanh saturator

Status: accepted, 2026-11-17.

## Context

The cubic soft clipper (ADR 0250) has a hard corner in its second derivative at `±1`, and it
holds flat past that point. Tape and valve models more often use `tanh`, which is smooth
everywhere and approaches its limit gradually. A drive setting sets how hard the signal is
pushed. Dividing by `tanh(drive)` keeps `±1` mapped to `±1`, so the output peak does not change
with the drive.

## Decision

- **The API.**
  - Python: `saturate(samples, drive)` in `dsp`.
  - C#: `Dsp.Saturate(samples, drive)`.
  - Real samples only.
- **The value.** `y = tanh(drive·x) / tanh(drive)`, evaluated in that order.
  - It is odd and memoryless.
  - Up to rounding, it is `±1` at `x = ±1`.
  - It tends to `x` as `drive → 0`.
  - `|y|` stays below `1/tanh(drive)`.
- **The rules.**
  - `drive` must be finite and `> 0`.
  - The samples must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from the stdlib `math.tanh`, an independent implementation.
  - `tanh` may differ by an ulp between the languages, so the tolerance is `rel 1e-13`.
