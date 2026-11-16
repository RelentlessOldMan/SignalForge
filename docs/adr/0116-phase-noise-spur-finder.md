# ADR 0116: Phase noise spur finder

Status: accepted, 2026-11-16. It adds the detection that
[ADR 0115](0115-phase-noise-spur-removal.md) left out, as a helper whose offsets feed
`spur_offsets`.

## Context

ADR 0115 removes spurs the caller names. Often the caller does not know them all: a
fractional-N synthesizer's spurs move with the channel, and a mains sideband sits wherever the
supply puts it. Instruments offer a spur table: each discrete line standing above the noise, with
its offset and level.

## Decision

- `phase_noise_spurs(samples, sample_rate, f_lo, f_hi, *, threshold_db=10.0, carrier=None,
  nperseg=None, window="blackman_harris", beta=None, width=None)` (C#
  `Measurements.PhaseNoiseSpurs`). It returns `PhaseNoiseSpurs`: `carrier_frequency` and
  `carrier_power` as for `phase_noise_ssb`, plus `offsets` and `levels_dbc`, one per spur in
  ascending frequency.
  - The carrier, its group and its half-width `w` come from the same Welch PSD and the same rules
    as `phase_noise_ssb`.
- **Search band.** The search covers bins whose offset `|f_j − carrier_frequency|` lies in
  `f_lo … f_hi`, on both sides, as for `integrated_phase_noise`.
  - The band must not reach past the spectrum.
  - A band bin with `|j − k_c| ≤ 2w + 1` is `invalid_argument`. That is the zone where ADR 0115
    could not remove a spur, so every spur found can be passed straight back.
- **The test is the removal rule's own line.** For a band bin `j`, `a = j − w − 1` and
  `b = j + w + 1`. A bin whose `a` or `b` is past the spectrum is not tested.
  - The bin powers `p` are the PSD times the bin width. Bins at or below `1e-20` of the total
    power are rounding error and count as zero, as in the tone metrics, so that the two languages
    agree on spectra with empty gaps.
  - `G = Σ_{a<i<b} p_i` is the group's power. `L = (2w + 1)(p_a + p_b)/2` is the power under the
    straight line that ADR 0115 would put there.
  - `j` is a spur when both of these hold:
    - It is the group's peak: `p_j > p_i` for `j − w ≤ i < j`, and `p_j ≥ p_i` for
      `j < i ≤ j + w`. A plateau's first bin wins, so a run of neighbouring candidates gives one
      spur.
    - `G > L·10^(threshold_db/10)`. The test is strict, so an empty group is never a spur.
  - Its offset is `f_j − carrier_frequency`, signed. Its level is
    `10·log10((G − L)/carrier_power)`, the power the removal would take away.
- **`threshold_db`** must be finite and positive, with a default of 10 dB. It is a ratio of group
  power to line power, not a level, so it does not depend on the PSD's scale or the segment
  length.
- **Why a line, not a median.** A median of neighbours is the usual detector. It needs a
  neighbourhood width and a median of an even count, and it sits low on a sloping skirt. The line
  between the group's edges is what ADR 0115 already fixes, and on the convex `1/f²` skirt of
  phase noise it lies above the curve. Noise therefore reads below the line, not above it.
- **No removal here.** The helper reports. The caller passes `abs(offsets)` to `spur_offsets`,
  and that removes both sides of each offset. On the side with no spur, the removal puts a line
  through noise, which changes the integral by about the noise's own curvature.

## Consequences

- **Vectors.** These are worked by hand from the bin spectrum of coherent lines, as in ADR 0115:
  Jacobi–Anger PM lines and spur tones, with each line's power in seven bins in the
  Blackman-Harris proportions. Cases cover:
  - every line in the band found, with exact levels
  - a spur on a neighbouring line's skirt
  - a weak line under a threshold that a lower threshold finds
  - a candidate whose edge is past the spectrum
  - real input
  - the error cases
- **Tests.** A spur placed on Wiener phase noise is found at its offset and level, and Wiener
  noise alone gives no spurs at 10 dB. Feeding the offsets to `integrated_phase_noise` recovers
  the integral without the spur.
