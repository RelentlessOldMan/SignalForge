# ADR 0138: Peak widths

Status: accepted, 2026-11-16. It extends the spectral peaks (ADR 0135).

## Context

A peak's width tells a tone from a broad hump and estimates a resonance's Q. Peak finders
measure the width at a level set by the prominence: `height − rel_height·prominence`. They
interpolate linearly between the bins where the PSD crosses that level. A fixed ratio such as
−3 dB is the other common choice, but on a peak over a floor it can cross below the floor or
never cross at all.

## Decision

- **The API.**
  - Python: `peak_widths(frequencies, psd, *, rel_height=0.5, min_prominence=0.0)`, returning
    a list of `PeakWidth(index, level, left, right, width)`.
  - C#: `Spectral.PeakWidths(frequencies, psd, relHeight, minProminence)`, returning an
    `IReadOnlyList<PeakWidth>` of the record `PeakWidth(Index, Level, Left, Right, Width)`.
  - There is one entry per `spectral_peaks` peak with the same `min_prominence`, in the same
    order.
- **The level.** `level = height − rel_height·prominence`, with `0 < rel_height ≤ 1`.
- **The crossings.**
  - For the left crossing, walk left from the run's first bin `i` to the first bin `k` with
    `x_k ≤ level`. The crossing is at `k + (level − x_k)/(x_{k+1} − x_k)` bins.
  - The right crossing mirrors it from the run's last bin.
  - `left` and `right` are those positions in Hz, `f_0 + position·δ`, and
    `width = right − left`.
- **Always found.** With `rel_height ≤ 1`, the level is at or above each side's base, so each
  walk ends before it reaches a higher bin or the edge. Rounding could push it past by an ulp; if
  so, the walk stops at the first or last bin.
- **The rules.**
  - `rel_height` must be finite with `0 < rel_height ≤ 1`.
  - The rest is validated as for `spectral_peaks`.
  - Anything else is `invalid_argument`.

## Consequences

- **The half-power width.** On a PSD whose peak's base is 0, `rel_height = 0.5` gives the
  half-power (−3 dB) width.
- **A plateau's width** includes the whole run.
- **Vectors.** These are worked by hand:
  - a triangle at half and full height, on a spaced grid.
  - an asymmetric peak.
  - nested peaks, where the smaller one's level is set by its own prominence.
  - a plateau.
  - a threshold.
  - the errors.
- **Tests.**
  - Scaling the PSD leaves the widths unchanged.
  - A Hann-windowed tone's −3 dB width is about 1.44 bins. It is measured zero-padded, so the
    main lobe is finely sampled, and off DC, since an edge bin is never a peak.
