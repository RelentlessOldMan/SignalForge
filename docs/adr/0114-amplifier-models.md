# ADR 0114: Saleh and Rapp amplifier models

Status: accepted, 2026-11-16. It goes with AM/AM and AM/PM, [ADR 0113](0113-am-am-am-pm.md), and
gain compression, [ADR 0112](0112-gain-compression.md).

## Context

A link simulation needs a power amplifier to measure against: something that compresses and, for
a travelling-wave tube, turns phase with drive. The two standard memoryless models are Saleh's
(a travelling-wave tube, with AM/AM and AM/PM) and Rapp's (a solid-state amplifier, AM/AM only,
with a knee whose sharpness is set by one parameter). Both act on the complex envelope.

## Decision

- Both are channel impairments in `signalforge.channel` and C# `Channel`. Each takes 1-D samples
  and returns complex samples of the same length; empty input gives empty output.
  - A real input is the complex value `x + 0j`, so a negative sample has phase π.
  - The samples are the complex baseband envelope. There is no bandpass mode: a real passband
    signal through these formulas is not a bandpass amplifier.
  - With `r = |x|`, both are `y = (x/r)·A(r)·e^{jΦ(r)}`, and `x = 0` gives `y = 0`.
- **Saleh**: `saleh_amplifier(samples, alpha_a, beta_a, alpha_phi, beta_phi)`, C#
  `Channel.SalehAmplifier`.
  - `A(r) = α_a r/(1 + β_a r²)`, `Φ(r) = α_φ r²/(1 + β_φ r²)` in radians.
  - Computed as `y = x·α_a/(1 + β_a r²)·e^{jΦ(r)}`, so no division by `r`.
  - `α_a > 0`, `β_a ≥ 0`, `β_φ ≥ 0`, `α_φ` any sign, all finite. No defaults: Saleh's fitted
    values (2.1587, 1.1517, 4.0033, 9.1040) are for his tube, not a general amplifier.
- **Rapp**: `rapp_amplifier(samples, gain, saturation, smoothness)`, C# `Channel.RappAmplifier`.
  - `A(r) = g r/(1 + (g r/A_sat)^{2p})^{1/(2p)}`, `Φ = 0`.
  - With `u = g r/A_sat`: for `u ≤ 1`, `y = x·g/(1 + u^{2p})^{1/(2p)}`; for `u > 1`,
    `y = (x/r)·A_sat/(1 + u^{−2p})^{1/(2p)}`. The second form keeps a large drive from
    overflowing `u^{2p}` and returns `A_sat` in the limit.
  - `g`, `A_sat` and `p` positive and finite.
- Samples are not checked: a non-finite sample gives a non-finite output, as in DC offset.

## Consequences

- **Vectors.** These are worked by hand from the formulas at chosen amplitudes and phases: the
  Saleh tube values; Rapp at `u` below, at and above 1 (at `u = 1`, `A = A_sat/2^{1/(2p)}`); a
  very large drive reads `A_sat`; a negative real sample; zero.
- **Tests.**
  - `am_am_pm` reads the curves back.
  - `gain_compression` finds Rapp's 1 dB point, `g r = A_sat (10^{p/10} − 1)^{1/(2p)}`.
  - Saleh's output amplitude peaks at `r = 1/√β_a` with `α_a/(2√β_a)`.
