# ADR 0113: AM/AM and AM/PM

Status: accepted, 2026-11-16. It goes with gain compression, [ADR 0112](0112-gain-compression.md).

## Context

A power amplifier's gain and its phase shift both change with the drive level. The two curves,
AM/AM and AM/PM, describe a memoryless device. Digital predistortion fits a model to them, and
the Saleh and Rapp models are written in terms of them. They are read from paired input and
output samples, by grouping the samples by input level.

## Decision

- Python `am_am_pm(input, output, edges_db)`, and C# `Measurements.AmAmPm(...)`.
  - The inputs are complex samples of the same length, at least 1, all finite.
  - `edges_db` gives the bin edges in dB of input amplitude, `20·log10|x|`. There are at least
    2 edges, finite and strictly ascending.
- **Bins.**
  - A sample with level `L` falls in bin `i` when `eᵢ ≤ L < eᵢ₊₁`. The last bin also takes its
    upper edge.
  - Samples outside every bin are not counted. That includes `x = 0`, whose level is `−∞`.
  - A level within rounding of an edge may fall on either side in the two languages. Vectors
    keep their samples clear of edges.
- **Per bin.**
  - `h` is the mean of the complex ratios `yₖ/xₖ` over the bin's samples, summed in order.
    The mean of the complex ratio is used, not the magnitude and angle averaged separately, so a
    bin that straddles a phase wrap still averages correctly.
  - `gain_db = 20·log10|h|`.
  - `phase_deg = atan2(Im h, Re h)·180/π`, in `(−180, 180]`.
  - An empty bin has gain and phase NaN and a count of 0. A bin whose `h` is 0 has a gain of
    `−∞` and a phase of 0.
- **The result** is `AmAmPm`. It has:
  - `levels_db`, the centre of each bin, `(eᵢ + eᵢ₊₁)/2`
  - `counts`, the number of samples in each bin
  - `gain_db` and `phase_deg`, one value per bin
- There is no small-signal reference. The caller subtracts the first bin, or any other, to get
  AM/PM relative to small signal. That choice depends on the sweep, so it is left to the caller.

## Consequences

- **Vectors.** These are worked by hand.
  - The Saleh model `A(r) = α_a r/(1 + β_a r²)`, `Φ(r) = α_φ r²/(1 + β_φ r²)` is applied to
    samples whose amplitude is the same within each bin, at several phases.
  - Each bin then reads `20·log10(A(r)/r)` and `Φ(r)` in degrees, by hand.
  - A bin is left empty. A sample at zero is not counted.
- **Tests.**
  - A linear gain with a fixed phase reads flat curves.
  - A Rapp-style limiter shows its compression, and agrees with `gain_compression`'s point when
    read through the same levels.
