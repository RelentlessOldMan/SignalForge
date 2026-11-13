# 0015: Tone metrics from one windowed spectrum

Date: 2026-11-13. Status: accepted.

## Context

SNR, SINAD, THD and ENOB of a single tone are the standard figures for a converter or a receiver
chain. Every tool computes them slightly differently: how the spectrum is taken, how many bins
around the tone count as the tone, where aliased harmonics land, whether DC counts as noise, and
whether noise is scaled up for the bins left out. Two implementations must agree on every one of
those choices, so they are fixed here.

## Decision

- **One spectrum, one segment.** The measurement is a periodogram of the whole input (`welch_psd`
  with `nperseg` equal to the length), so it reuses the PSD's window, scaling and sidedness and
  needs no new numerical code. Bin power is `PSD·bin_width`; with the PSD's scaling the bins of a
  tone add up to its power for any window, and white noise reads its power in expectation.
- **Bins are grouped, each bin counted once**, in a fixed order: DC, the fundamental, harmonics
  2 … `num_harmonics + 1`, and everything left is noise. A group is the nearest bin ± a half-width
  `w`, clipped at the ends of the spectrum and skipping bins an earlier group took. Earlier groups
  win, so a harmonic that lands on DC or on the fundamental adds nothing twice.
- **Default half-width from the window**: `K` bins for a `K`-term cosine sum (an on-bin tone fills
  `±(K−1)` bins, plus one bin of guard), and `⌈√(1 + (β/π)²)⌉` for Kaiser (its main-lobe
  half-width). The default window is Blackman-Harris, whose sidelobes (−92 dB) are below what most
  measurements need to see.
- **The fundamental's frequency is the power-weighted centroid of its group**, and harmonics are
  placed at multiples of that, aliased into the spectrum's range. Tones off a bin center are then
  handled without interpolation formulas tied to one window.
- **DC is its own group, reported but in neither noise nor distortion.** Noise is the plain sum of
  the remaining bins, not scaled for the bins the groups took: the scaling depends on the noise
  being white, and leaving it out keeps the number a sum anyone can check.
- **Formulas**: SNR `10·log10(S/N)`, SINAD `10·log10(S/(N+H))`, THD `10·log10(H/S)` (a ratio of
  powers, as dB), ENOB `(SINAD − 10·log10 1.5)/(20·log10 2)`, the full-scale-sine formula. No signal
  power is an error; zero noise or distortion gives ±∞, not an error.
- Implemented from the definitions; no third-party code.

## Consequences

- Results depend on the window and width, which are parameters with stated defaults, so a number
  can always be reproduced.
- A tone close to DC or Nyquist loses part of its group to clipping or to DC; the centroid is then
  biased. Measurements should keep the tone a few groups away from both.
- Spurs that are not harmonics count as noise; SFDR and spur search come later as their own
  measurement.
