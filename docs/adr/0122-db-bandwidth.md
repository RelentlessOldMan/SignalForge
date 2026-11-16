# ADR 0122: x dB bandwidth

Status: accepted, 2026-11-16. It extends the spectral measurements (conventions: Spectra).

## Context

Spectrum analyzers and emission masks give a signal's width as the span between the points where
the PSD has fallen `x` dB below its peak. The usual values are 3 dB, 6 dB, and 26 dB for
emission masks. Occupied bandwidth (a power fraction) and the RMS bandwidth (a moment) are
different measures, and neither one is this.

## Decision

- Python `db_bandwidth(frequencies, psd, drop_db, *, band=None)` and C#
  `Spectral.DbBandwidth(frequencies, psd, dropDb, band)`.
- **The bins.** The bins are validated as for channel power, with no span.
  - With `band = (low, high)`, only bins whose centers lie in `[low, high]` take part.
  - Band edges must be finite with `low < high`, and at least one bin must lie in the band.
- **The peak.** The peak is the largest PSD among those bins, the first one on ties. Its PSD
  must be positive.
- **The edges.**
  - The threshold is `t = peak·10^{−drop_db/10}`.
  - From the peak, walk down in frequency to the first bin `i` with `psd[i] ≤ t`. The lower
    edge lies between bins `i` and `i + 1`, interpolated linearly in **power**:
    `f_i + (t − psd[i])/(psd[i+1] − psd[i])·Δ`. The upper edge is found the same way, walking up.
  - If no bin in the band falls to `t` on a side, the measurement fails with
    `invalid_argument`. It does not guess an edge.
- **The result.** `DbBandwidth(peak_frequency, peak_psd, lower, upper, bandwidth = upper −
  lower)`.
- `drop_db` must be finite and positive.

## Consequences

- **Interpolation in power.** Interpolating in power, not in dB, keeps a zero bin usable: its
  dB value is `−∞`. The cost is a small bias on curved skirts, which shrinks as the bins get
  finer. The bin sits strictly above `t` next to `i`, so the division is never by zero. A bin
  exactly at `t` is the edge.
- **The first crossing only.** Walking stops at the first crossing, so a ripple that dips below
  `t` inside the main lobe ends the walk there, as an analyzer's marker search does. To skip a
  side lobe, the caller can restrict the band.
- **Vectors.** These are short PSDs worked by hand: a symmetric and an asymmetric triangle, a
  tie at the peak, an edge exactly on a bin, a band that hides a larger peak, and the errors.
- **Tests.**
  - A finely sampled Gaussian PSD gives `2σ·sqrt(x·ln 10 / 5)`.
  - A rectangle gives its width up to one bin.
  - Scaling the PSD changes nothing but the peak.
  - A dip inside the main lobe ends the walk.
