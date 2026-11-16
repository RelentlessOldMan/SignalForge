# ADR 0118: Noise power ratio

Status: accepted, 2026-11-16. It builds on channel power and ACPR, [ADR 0019](0019-acpr.md).

## Context

The two-tone functions read discrete products, but an amplifier carrying many channels is tested
with a wideband load: noise or a dense multitone across the band, with a narrow notch cut in it.
Distortion fills the notch. The noise power ratio (NPR) is the loaded spectral density over the
density left in the notch, and it captures every order of distortion at once.

## Decision

- Python `noise_power_ratio(frequencies, psd, band, notch, *, span=None)`, and C#
  `Spectral.NoisePowerRatio(...)`. Like `acpr`, it reads a PSD the caller computed, so the
  window and averaging stay the caller's choice.
  - `band = (low, high)` is the loaded band and `notch = (low, high)` the notch, both in Hz.
- **The powers** come from the channel power rule (each bin counted by the fraction of its
  clipped width inside), with the same `span`.
  - The loaded power is the channel power of `[band.low, notch.low]` plus that of
    `[notch.high, band.high]`. It is summed directly, not taken as band minus notch, so rounding
    cannot leave a small negative.
  - `loaded_density` is the loaded power over its width, `(notch.low − band.low) + (band.high −
    notch.high)`.
  - `notch_density` is the notch's channel power over `notch.high − notch.low`.
- **The result** is `NoisePowerRatio(loaded_density, notch_density, npr_db)`, with
  `npr_db = 10·log10 loaded_density − 10·log10 notch_density`.
  - It is taken as a difference of logs, as ACPR's ratios are, so a deep notch does not
    underflow.
  - An empty notch gives `+∞`.
- **The rules**:
  - Every edge must be finite, and `band.low < notch.low < notch.high < band.high`. So both
    sides of the loaded band have width.
  - The band must lie inside the spectrum, with ACPR's slack of `1e-9` of the widest bin.
  - The loaded density must be `> 0`.
  - Anything else is `invalid_argument`.

## Consequences

- **One notch only.** Several notches, or a notch per channel, can be added later, as a list
  of notches.
- **Vectors.** These are worked by hand on short piecewise-constant PSDs, as for ACPR. Edges
  fall on bin boundaries and inside bins, on a one-sided PSD with a span and on a two-sided one,
  with an empty notch for `+∞`.
- **Tests.**
  - A coherent multitone, every bin of the band loaded except the notch, goes through
    `y = x + a₃x³`.
  - The test expands the cubic exactly, independently of SignalForge, to get the lines that
    land in the notch. It checks the NPR against a periodogram with a rectangular window, where
    each line is exactly one bin.
