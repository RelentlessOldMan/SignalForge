# ADR 0298: Reverse delay

Status: accepted, 2026-11-17.

## Context

A reverse delay records a stretch of the input and plays it back backwards while the next
stretch records. Each phrase is followed by its own mirror image, one block late. Delay pedals
offer it as a mode. It needs no interpolation: it is a fixed reordering of the samples.

## Decision

- **The API.**
  - Python: `reverse_delay(samples, block, mix)` in `dsp`.
  - C#: `Dsp.ReverseDelay(samples, block, mix)`.
  - `block` is an integer `B` in samples. Real samples only.
- **The value.**
  - Write `n = q·B + r` with `0 ≤ r < B`.
  - For `q ≥ 1`, `wet[n] = x[(q − 1)·B + (B − 1 − r)]`, the previous block backwards. For the
    first block, `wet[n] = 0`.
  - A last block cut short by the end of the signal plays the start of the reversed previous
    block, as far as it goes.
  - `y = (1 − mix)·x + mix·wet`, the dry/wet blend of the other effects.
  - The block edges are hard. A caller who wants no clicks crossfades or windows the wet
    signal.
- **The rules.**
  - The samples must be real, finite and at least one.
  - `block` at least 1. At 1 the wet signal is the input delayed by one sample.
  - `mix` in [0, 1].

## Consequences

- **Vectors.**
  - Expected values come from the index rule, transcribed in the stdlib, with one product and
    blend in floats per sample.
  - The tolerance is `abs 1e-15, rel 1e-15`.
