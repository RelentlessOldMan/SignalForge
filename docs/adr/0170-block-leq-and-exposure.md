# ADR 0170: Short Leq series and sound exposure

Status: accepted, 2026-11-16. It goes with the time weighting (ADR 0166) and the exceedance
levels (ADR 0169).

## Context

Two more integrating measures are common:

- A series of short equivalent levels, such as `L_eq,1s` or `L_eq,100ms`. Each is the mean of
  `|x|²` over a block.
- The sound exposure `E = ∫ p² dt`, in Pa²·s, behind the sound exposure level
  `SEL = 10 log10(E / (p0²·1 s))`.

Implementations differ on three points:

- how a block length that is not a whole number of samples is rounded;
- whether a partial last block is kept;
- the units of the exposure.

## Decision

- **The API.** In `measurements`, for real and complex samples:
  - Python: `block_leq(samples, sample_rate, duration)`; C#: `Measurements.BlockLeq`.
  - Python: `sound_exposure(samples, sample_rate)`; C#: `Measurements.SoundExposure`.
- **`block_leq`.**
  - The block length is `N = ⌊duration·fs + 1/2⌋` samples, which must be at least 1.
  - The result is the mean of `|x|²` over each of the `⌊len/N⌋` consecutive, non-overlapping
    blocks.
  - A partial last block is dropped. An input shorter than `N` gives an empty result.
- **`sound_exposure`.**
  - The result is `Σ|x[n]|² / fs`, the rectangle-rule integral, in the units of `|x|²` times
    seconds.
  - An empty input gives 0. The caller takes SEL with `lin_to_db`, against `p0²·1 s`.
- **The rules.**
  - The samples are one-dimensional and finite.
  - `sample_rate` and `duration` are finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **Partial blocks are lost.** A partial last block is not reported. A caller who needs it
  pads the input.
- **Vectors are hand sums over short series.** The cases are:
  - an exact block length;
  - a rounded block length;
  - a dropped tail;
  - complex samples;
  - an input shorter than one block;
  - the empty exposure;
  - the errors.
