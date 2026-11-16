# ADR 0115: Phase noise with spurs removed

Status: accepted, 2026-11-16. It extends the phase noise measurement,
[ADR 0108](0108-phase-noise-measurement.md), and integrated phase noise,
[ADR 0109](0109-integrated-phase-noise.md).

## Context

A real oscillator's spectrum has discrete spurs next to its phase noise: reference feedthrough,
mains sidebands, fractional-N spurs. `phase_noise_ssb` and `integrated_phase_noise` read a spur as
noise. A spur is a line, not a density, so it inflates the integrated jitter and makes `L(f)` at
its offset meaningless. Instruments offer to suppress spurs before integrating.

## Decision

- Both functions take a keyword `spur_offsets` (C# `spurOffsets`, a `double[]?`): the spurs'
  offsets from the carrier in Hz. It is 1-D, every value finite and positive. The default is
  none, and an empty list is the same as none. The results do not change shape.
- **The spurs are named, not detected.** Automatic detection (a bin standing a threshold above
  its neighbours' median) depends on the threshold, the neighbourhood and ties, all of which the
  two languages would have to match bin for bin, and it can remove a real noise bump. The caller
  usually knows where its spurs are: the reference frequency, the mains, the channel step.
  Detection can come later as a helper that returns offsets for this argument.
- **Removal** works on a copy of the Welch PSD, before the sidebands or the band are read.
  - The offsets are taken in the order given, and for each, the side `carrier_frequency − o` first,
    then `carrier_frequency + o`.
  - A side outside the spectrum (the same test as an offset's reach) is skipped.
  - Otherwise `s` is the bin nearest that frequency, `w` the carrier group's half-width (the
    window's main lobe), and `a = s − w − 1`, `b = s + w + 1` the bins just outside the spur's
    group.
  - Each bin `j` with `a < j < b` in the spectrum gets `p_a + (p_b − p_a)·(j − a)/(2w + 2)`,
    computed in that order: a straight line, in linear PSD, between the two edge bins.
  - An edge past the spectrum takes the other edge's value. At least one edge is always inside,
    because of the next rule.
  - `|s − k_c| ≤ 2w + 1` is `invalid_argument`: the spur's group or its edge would touch the
    carrier group.
  - The edges are read as the PSD stands at that point, so a spur next to an earlier one
    interpolates from the already cleaned values. Overlapping spurs are allowed.
- **Linear, not in dB.** A line in dB is better on a steep slope, but it cannot pass through a
  zero bin, and over a group of a few bins the difference is small. Linear power keeps the
  vectors exact.

## Consequences

- **Vectors.** These are worked by hand, as for ADRs 0108 and 0109: carriers with pure
  sinusoidal phase modulation (Jacobi–Anger lines) plus an added spur tone, all coherent, so
  each line's power falls in seven bins in the window's known proportions,
  `c_d² / (a₀² + (a₁² + a₂² + a₃²)/2)` with `c₀ = a₀` and `c_{±d} = a_d/2`. The generator builds
  that bin spectrum, applies the rule above, and sums. Cases cover:
  - the spur kept and removed
  - an edge on a neighbouring line's skirt
  - two overlapping spurs in order
  - a side past the spectrum
  - the carrier-zone error
- **Tests.**
  - Wiener phase noise of known linewidth plus a spur: with removal the integral matches the
    run without the spur; without removal it is higher by the spur's power.
  - Removing no spurs changes nothing.
