# ADR 0136: Peak interpolation

Status: accepted, 2026-11-16. It extends the spectral peaks (ADR 0135).

## Context

A peak found on the bin grid can be up to half a bin from the tone. The usual refinement fits a
parabola through the peak bin and its two neighbours, then takes the vertex.

- On the PSD itself, the fit is exact for a parabolic peak.
- On the PSD in dB, it is exact for a Gaussian peak. That shape is close to the main lobe of most
  windows, so the dB fit is the more accurate one for windowed spectra.

Libraries differ on the scale. They also differ on what they do when the peak bin is not a
maximum.

## Decision

- **The API.**
  - Python: `interpolate_peak(frequencies, psd, index, *, scale="db")`, returning
    `PeakEstimate(frequency, height, offset)`.
  - C#: `Spectral.InterpolatePeak(frequencies, psd, index, scale)`, where `scale` is the
    `enum PeakScale { Decibel, Linear }` and defaults to `Decibel`. It returns the record
    `PeakEstimate(Frequency, Height, Offset)`.
- **The fit.**
  - `α`, `β` and `γ` are the values at `index − 1`, `index` and `index + 1`. For `"db"` they are
    `10 log10` of the PSD; for `"linear"` they are the PSD itself.
  - `offset = (α − γ) / (2(α − 2β + γ))`, in bins.
  - `frequency = f_index + offset·δ`, where `δ` is the bin spacing.
  - The vertex is `β − (α − γ)·offset/4`.
  - `height` is that vertex. For `"db"` it is converted back to PSD units, `10^(vertex/10)`.
- **The range.** The peak bin must be at least as high as each neighbour, and the curvature
  `α − 2β + γ` must be negative. Then `|offset| ≤ 1/2`. Two equal top bins give
  `offset = ±1/2`, their middle. That is where `spectral_peaks` puts a plateau's frequency.
- **The rules.**
  - `frequencies` and `psd` are validated as for `spectral_peaks`.
  - `index` must be an integer with `1 ≤ index ≤ n − 2`, because the edge bins have only one
    neighbour.
  - The bin must not be lower than either neighbour, and the three bins must not be flat.
  - For `"db"`, all three values must be positive.
  - `scale` must be `"db"` or `"linear"`.
  - Anything else is `invalid_argument`.

## Consequences

- **Bias.** On a real window's main lobe, the dB fit leaves a small bias that depends on the
  window and the offset. This function does not correct it.
- **Vectors.** The expected vertices are analytic:
  - parabolas sampled at known offsets, on the linear scale.
  - Gaussians sampled at known offsets, on the dB scale, including the default scale.
  - a symmetric peak.
  - two equal top bins. For the values 1, 2, 2 the dB height is `2^(9/8)`.
  - a zero neighbour, on the linear scale.
  - the errors.
- **Tests.**
  - The dB fit recovers a Gaussian's centre as it shifts across a bin.
  - Scaling the PSD scales the height and leaves the offset unchanged.
  - The fit finds a Hann-windowed tone between bins to within 0.05 bin.
