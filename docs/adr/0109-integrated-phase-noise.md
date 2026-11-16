# ADR 0109: Integrated phase noise and RMS jitter

Status: accepted, 2026-11-16. It builds on the single-sideband phase noise measurement,
[ADR 0108](0108-phase-noise-measurement.md).

## Context

`L(f)` is a curve. The single numbers quoted beside it are the integrated phase noise over an
offset band and the RMS jitter it implies at the carrier: `φ_rms = √(2∫L(f)df)` rad, and
`t_rms = φ_rms/(2πf_c)`. They need a decision on which bins the band holds, on the two sidebands,
and on spurs.

## Decision

- Python `integrated_phase_noise(samples, sample_rate, f_lo, f_hi, *, carrier=None,
  nperseg=None, window="blackman_harris", beta=None, width=None)`, and C#
  `Measurements.IntegratedPhaseNoise(...)`. Both take real or complex samples.
- The spectrum, the carrier, its group, `carrier_power` and `carrier_frequency` are exactly those
  of `phase_noise_ssb`, with the same argument rules.
- **The band.** It is the whole bins whose centre `f_k` has `f_lo ≤ |f_k − f_c| ≤ f_hi`, on both
  sides of the carrier. No partial bins are taken, so a caller who wants exact edges puts them
  between bins.
  - `0 < f_lo < f_hi`, both finite.
  - `f_c − f_hi` and `f_c + f_hi` must lie in the spectrum's range, as for an offset. A band bin
    inside the carrier group is `invalid_argument`.
- **The integral.** `ratio = Σ PSD_k·Δf / carrier_power` over the band bins of both sides.
  - Summing both sides is `2∫L df`, the double-sideband total, without the mean. A spectrum that
    is not symmetric is then counted as it is.
  - `integrated_dbc = 10·log10 ratio`, which is `−∞` for no power.
  - `phase_rms = √ratio`, in radians. This is the small-angle reading: `φ_rms² ≈` the sideband
    power over the carrier when the modulation is small. It is not corrected for large indices,
    as instruments don't.
  - `jitter_rms = phase_rms/(2π|f_c|)`, in seconds. For complex baseband input `f_c` is the
    offset from the centre frequency, so the caller rescales by the real carrier.
  - When `f_c = 0` exactly, `jitter_rms` is `+∞`, or `0` if `phase_rms` is `0`.
- **Spurs.** A discrete line in the band adds its whole power, provided all its bins fall in the
  band. That is what an analyser's integration does, and no spur is removed.
- The result is `IntegratedPhaseNoise`, with these fields:
  - `carrier_frequency`
  - `carrier_power`
  - `f_lo`, `f_hi`
  - `integrated_dbc`
  - `phase_rms`
  - `jitter_rms`

## Consequences

- **Vectors.** Pure phase modulation `m·sin(2πf_m n/fs)` has lines `J_k(m)²` at `k·f_m`, by
  Jacobi–Anger.
  - With coherent rates, the 4-term Blackman–Harris window puts each line's whole power in seven
    bins. With band edges between lines, `ratio = Σ J_k²/J_0²` over the lines in the band, both
    signs of `k`, exactly.
  - The cases are real and complex, with one segment and several.
- **Tests.**
  - A small index gives `φ_rms ≈ m/√2`, the textbook RMS of a sine.
  - Wiener phase noise integrates by hand. `∫S df = (1/π)·arctan(((1+ρ)/(1−ρ))·tan(πf/fs))`
    between the edges, and it is checked as a statistic.
