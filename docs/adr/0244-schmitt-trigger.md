# ADR 0244: Schmitt trigger

Status: accepted, 2026-11-17.

## Context

A plain comparator chatters when a noisy signal lingers near its threshold. A Schmitt trigger has
two thresholds. It goes high above the upper one and low below the lower one, and it holds its
state between them. Gates, squelch circuits and edge detectors all use one.

## Decision

- **The API.**
  - Python: `schmitt_trigger(samples, low, high)` in `dsp`, returning `uint8`.
  - C#: `Dsp.SchmittTrigger(samples, low, high)`, returning `byte[]`.
  - Real samples only.
- **The value.**
  - The state starts at 0.
  - `x[n] > high` sets the state to 1. `x[n] < low` sets it to 0. Otherwise the state is kept.
  - Both comparisons are strict, so a sample exactly on a threshold keeps the state.
  - The output is the state after each sample.
- **The rules.**
  - `low` and `high` must be finite, with `low < high`.
  - The samples must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values are 0 and 1 from the definition, run on samples that are exact binary
    fractions.
  - The cases include samples that sit exactly on each threshold.
