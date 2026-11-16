# ADR 0108: Single-sideband phase noise measurement

Status: accepted, 2026-11-16. It measures what [ADR 0036](0036-phase-noise.md) models.

## Context

An oscillator's phase noise is quoted as `L(f)`: the noise power in 1 Hz at an offset `f` from
the carrier, relative to the carrier's power, in dBc/Hz. SignalForge can add phase noise, but it
cannot yet measure it. The measurement needs a decision on the spectrum, the carrier and the
sidebands.

## Decision

- Python `phase_noise_ssb(samples, sample_rate, offsets, *, carrier=None, nperseg=None,
  window="blackman_harris", beta=None, width=None)`, and C# `Measurements.PhaseNoiseSsb(...)`.
  Both take real or complex samples.
- The spectrum is `welch_psd(samples, sample_rate, nperseg=nperseg, window=window, beta=beta)`,
  with the PSD's defaults for the rest. That is one-sided for real input and two-sided for
  complex.
- **The carrier.**
  - With no `carrier` given, it is the first bin with the largest PSD. With `carrier` given, it
    is the bin nearest that frequency, under the fundamental's rules from the tone metrics.
  - The carrier's group is the bins within the half-width `w` of it, clipped to the spectrum.
    `w` is set by the window as in the tone metrics, unless `width` is given.
  - `carrier_power` is the group's power (PSD · bin width, summed), and `carrier_frequency` is
    its power centroid.
  - No DC group is claimed, because a complex baseband carrier usually sits at 0 Hz.
  - A carrier with no power is `invalid_argument`.
- **The sidebands.** For each offset `o`, the PSD is read at the bins nearest
  `carrier_frequency ± o`.
  - `L(o) = 10·log10(mean of the two PSD values / carrier_power)`, in dBc/Hz. It is `−∞` when
    both values are zero.
  - Averaging the two sidebands is the usual practice. It also halves the variance.
  - This is the definition of `L`, the sideband density relative to the carrier. So no
    small-angle step is taken, although `L ≈ S_φ/2` when the modulation is small.
- **Arguments.**
  - `offsets` is one-dimensional, non-empty, and finite and positive.
  - Both `carrier_frequency ± o` must lie within the spectrum's range (`0 ≤ f ≤ fs/2` for
    real input, `−fs/2 ≤ f < fs/2` for complex, as the bins run), and outside the carrier group, so `|k − k_c| > w`.
    Otherwise the call is `invalid_argument`.
  - The samples follow the tone metrics' rules: at least two, and a finite spectrum.
- The result is `PhaseNoise`, with these fields:
  - `carrier_frequency`
  - `carrier_power`
  - `offsets`
  - `l_dbc_hz`
- A discrete spur reads as its power divided by the window's ENBW. That is how a spectrum
  analyser's noise marker reads it.

## Consequences

- **Vectors.** Pure phase modulation `e^{jm·sin(2πf_m n/fs)}`, coherent with the segments, has
  lines `J_k(m)²` at `k·f_m`, by the Jacobi–Anger expansion.
  - With a 4-term Blackman–Harris window, each line sits alone in its bins. So
    `L(k·f_m) = J_k² / (J_0² · ENBW)` exactly, with `ENBW = (fs/N)(a₀² + (a₁² + a₂² + a₃²)/2)/a₀²`
    for the periodic window.
  - The vectors compute this from the window's definition and the Bessel series. The cases
    are real and complex, with one segment and several.
- **Tests.** Wiener phase noise has the discrete Lorentzian
  `S(ω) = (1 − ρ²)/(1 − 2ρ cos ω + ρ²)`, with `ρ = e^{−σ²/2}`. `L` plus the carrier power in dB
  must match it, as a statistic, in both languages.
