# ADR 0137: Find tones

Status: accepted, 2026-11-16. It builds on the spectral peaks (ADR 0135) and the peak
interpolation (ADR 0136).

## Context

Finding a spectrum's main tones means ranking its peaks by prominence, keeping the first few,
and refining each one between bins. Composing the two existing functions leaves three questions
open:

- how ties are broken;
- what order the results come in;
- what happens to a peak that the interpolation rejects. That is a plateau of three or more bins,
  which is flat at its middle, or a zero neighbour on the dB scale.

## Decision

- **The API.**
  - Python: `find_tones(frequencies, psd, count, *, min_prominence=0.0, scale="db")`, returning
    a list of `Tone(index, frequency, height, prominence)`.
  - C#: `Spectral.FindTones(frequencies, psd, count, minProminence, scale)`, returning an
    `IReadOnlyList<Tone>` of the record `Tone(Index, Frequency, Height, Prominence)`.
- **The ranking.**
  - The peaks are those of `spectral_peaks` with the same `min_prominence`.
  - They are sorted by prominence, highest first. Ties go to the lower frequency.
  - The first `count` peaks are kept. There may be fewer.
  - The results are in that ranked order.
- **The refinement.**
  - `index` and `prominence` are the peak's.
  - `frequency` and `height` are those of `interpolate_peak` at the peak's index, on `scale`.
  - A two-bin plateau's index is its first bin, so the fit lands at its middle.
  - When the fit is not defined, the tone keeps the peak's grid frequency and height. That
    happens when the three bins are flat, or when one of them is 0 on the dB scale.
- **The rules.**
  - `count` must be an integer, at least 1.
  - `scale` must be `"db"` or `"linear"`.
  - The rest is validated as for `spectral_peaks`.
  - Anything else is `invalid_argument`.

## Consequences

- **The fit uses only three bins.** So a tone's vertex depends only on its own peak bin and
  that bin's two neighbours.
- **Vectors.** These are worked by hand or analytically:
  - two Gaussian peaks, sampled only on their three bins over a floor, so each vertex is the
    Gaussian's centre and height. They are taken at several counts and a threshold.
  - a single bin with a zero neighbour, and a three-bin plateau, on the dB scale (grid values)
    and on the linear scale.
  - an even plateau.
  - a tie.
  - the errors.
- **Tests.**
  - The tones are the interpolated top peaks.
  - Two windowed tones in noise are found within 0.05 bin, the louder first.
