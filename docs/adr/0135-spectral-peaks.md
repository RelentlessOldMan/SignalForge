# ADR 0135: Spectral peaks

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

Listing the tones in a spectrum starts with its local maxima, ranked by how far each one stands
out from its surroundings. That measure is the topographic prominence that peak finders use.
Libraries differ in four ways:

- how they treat plateaus;
- how they treat the first and last bins;
- what a peak's position is;
- whether a prominence base may cross a taller peak.

## Decision

- **The API.**
  - Python: `spectral_peaks(frequencies, psd, *, min_prominence=0.0)`, returning a list of
    `SpectralPeak(index, frequency, height, prominence)` in order of frequency.
  - C#: `Spectral.SpectralPeaks(frequencies, psd, minProminence)`, returning an
    `IReadOnlyList<SpectralPeak>` of the record `SpectralPeak(Index, Frequency, Height,
    Prominence)`.
- **A peak.** A peak is a maximal run `i..j` of equal PSD values with both neighbours strictly
  lower. A single bin is a run of length 1.
  - The first and last bins are never peaks, because the PSD's value beyond them is unknown.
  - A run that rises into a higher value is a shoulder, not a peak.
- **Its position.**
  - `index = ⌊(i + j)/2⌋`.
  - `frequency = (f_i + f_j)/2`, which is the run's true middle, even when the run has an even
    length.
  - `height` is the run's value.
- **Its prominence.**
  - On the left, walk from `i` until the first bin strictly higher than `height`, or to the
    first bin of the PSD. The left base is the lowest value on that stretch, from `i` but not
    including the higher bin.
  - The right base is found the same way from `j`.
  - `prominence = height − max(left base, right base)`.
  - It is always positive.
- **The threshold.** Peaks with `prominence ≥ min_prominence` are kept.
- **The rules.**
  - `frequencies` and `psd` are validated as for `channel_power`, with at least two bins.
  - `min_prominence` must be finite and `≥ 0`.
  - Anything else is `invalid_argument`.

## Consequences

- **No band argument.** A band is a slice of the arrays, which the caller can take. The slice's
  end bins then cannot be peaks.
- **No interpolation.** The positions are on the bin grid. Interpolating between bins is a
  separate decision; `kay_frequency` covers single tones.
- **Vectors.** These are worked by hand:
  - a single peak.
  - nested peaks, where the smaller one's base stops at the taller one.
  - odd and even plateaus.
  - edges that are not peaks.
  - a shoulder.
  - a threshold.
  - a monotone PSD with no peaks.
  - the errors.
- **Tests.**
  - Scaling the PSD scales the heights and prominences.
  - Every peak's height is at least its prominence.
  - Each tone in a noisy spectrum is found as the most prominent peak.
