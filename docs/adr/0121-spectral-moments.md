# ADR 0121: Spectral centroid and RMS bandwidth

Status: accepted, 2026-11-16. It extends the spectral measurements (conventions: Spectra).

## Context

Occupied bandwidth gives the edges that hold a fraction of the power. The PSD's first two
moments are a different summary.

- The **centroid** is the power-weighted mean frequency, which shows a carrier offset.
- The **RMS bandwidth**, or Gabor bandwidth, is the power-weighted spread about the centroid.
  It sets the Cramér-Rao bound on time-of-arrival accuracy, and it is a common spread measure.

## Decision

- Python `spectral_moments(frequencies, psd, *, band=None, span=None)` and C#
  `Spectral.SpectralMoments(frequencies, psd, band, span)`.
- **The density.** The PSD is taken as constant over each bin, as the channel power rule takes
  it.
  - Bin `k` has edges `[left_k, right_k]` (same validation, same `span`) and density
    `d_k = P_k / (right_k − left_k)`, where `P_k` is its power. A span-clipped edge bin keeps its
    whole power.
  - The moments are the exact integrals of this step density over `band = (low, high)`, which is
    the whole spectrum by default. Each bin contributes over its overlap `[a_k, b_k]`.
- **The result.**
  - `power = Σ d_k·(b_k − a_k)`.
  - `centroid = Σ d_k·(b_k² − a_k²)/2 / power`.
  - `rms_bandwidth = sqrt(Σ d_k·((b_k − c)³ − (a_k − c)³)/3 / power)`, about the centroid `c`.
    This is computed about `c`, not as `E f² − c²`, so that a narrow band far from 0 Hz does not
    cancel.
  - The result is `SpectralMoments(power, centroid, rms_bandwidth)`.
- **The rules.**
  - The band follows spectral flatness: finite edges with `low < high`, inside the spectrum
    within ACPR's slack.
  - `power > 0` is required.
  - Anything else is `invalid_argument`.

## Consequences

- **Not the bin-center sum.** The moments are not `Σ f_k·P_k`. That sum gives a variance
  `Δ²/12` smaller per bin, and it cannot weight a cut bin consistently. With the step density, a
  flat band of width `B` has an RMS bandwidth of exactly `B/√12`, however the bins fall, and
  `power` equals channel power over the same band.
- **Vectors.** These are short PSDs worked by hand in exact fractions: flat, a single bin
  (`Δ/√12`), two separated bins, an asymmetric pair, a cut band, a clipped span, and the errors.
  The generator works from `E f²`, an independent route to the same variance.
- **Tests.**
  - A rectangular PSD of width `B` gives `B/√12` and its center.
  - A Gaussian-shaped PSD sampled finely gives `sqrt(σ² + Δ²/12)`, its `σ` plus the step's spread.
  - Shifting the frequency axis shifts only the centroid.
  - `power` equals `channel_power` over the same band.
