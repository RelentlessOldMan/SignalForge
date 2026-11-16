# ADR 0126: Spectral skewness and kurtosis

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

The centroid and RMS bandwidth ([ADR 0121](0121-spectral-moments.md)) are a band's first two
moments. Two standardized moments come next:

- The skewness says which side the power leans to.
- The kurtosis says how peaked the band is.

Both are standard audio features. Libraries often take them from bin centers alone. A step
density integrated exactly instead gives a flat band the uniform distribution's values: skewness
0 and kurtosis 9/5.

## Decision

- Python `spectral_shape(frequencies, psd, *, band=None, span=None) -> SpectralShape(skewness,
  kurtosis)` and C# `Spectral.SpectralShape(frequencies, psd, band, span)`, with the record
  `SpectralShape(Skewness, Kurtosis)`.
- **The model.** This is the step density and pieces `[a_k, b_k]` of the spectral moments, with
  `power` and centroid `c` as there.
- **The central moments.** For `j = 2, 3, 4`,
  `m_j = Σ d_k ((b_k − c)^{j+1} − (a_k − c)^{j+1}) / (j + 1) / power`, integrated about the
  centroid.
- **The result.** `skewness = m3 / m2^{3/2}` and `kurtosis = m4 / m2²`. The kurtosis is not the
  excess kurtosis: a flat band gives 9/5.
- **The rules.**
  - The band rules are those of spectral flatness.
  - `power > 0` and `m2 > 0` are required.
  - Anything else is `invalid_argument`.

## Consequences

- **Spread.** A step density with power always has a positive spread, so `m2 > 0` only guards
  against rounding.
- **Scaling.** Both values are unchanged by scaling the PSD and by shifting or stretching the
  frequency axis. A mirrored PSD flips the sign of the skewness.
- **Vectors.** These are worked with Fractions by raw moments `E f^j`, expanded binomially about
  the centroid. That route differs from the libraries':
  - A flat band gives 0 and 9/5.
  - A single bin gives the same, since it is flat on its own.
  - Two ends give kurtosis below 9/5.
  - Uneven PSDs.
  - A cut band.
  - The span.
  - The errors.
- **Tests.**
  - Mirroring flips the skewness.
  - Shifting and scaling the axis change nothing.
  - A sampled Gaussian PSD of spread `s` bins has skewness 0. Its kurtosis is `m4/m2²` with
    `m2 = s² + 1/12` and `m4 = 3s⁴ + s²/2 + 1/80`, which is near 3. Each step adds a bin's
    uniform spread.
  - A flat PSD, cut by a band, gives 0 and 9/5.
