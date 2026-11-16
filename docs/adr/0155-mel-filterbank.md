# ADR 0155: Mel filterbank

Status: accepted, 2026-11-16. It builds on the mel scale (ADR 0154).

## Context

A mel filterbank is a set of overlapping triangles on the one-sided FFT bins, equally spaced in
mel. It turns a power spectrum into band energies, and it is the step before MFCCs.
Implementations differ on four points:

- the edges, and what the upper edge defaults to;
- whether the triangles are evaluated at the bin frequencies (librosa) or snapped to whole bins
  (HTK);
- the normalization;
- what happens to a filter that catches no bin.

## Decision

- **The API.**
  - Python: `mel_filterbank(n_filters, nfft, sample_rate, min_frequency=0.0,
    max_frequency=None, *, scale="htk", area_normalized=False)`, in `spectral`. It returns an
    `(n_filters, nfft//2 + 1)` float array.
  - C#: `Spectral.MelFilterbank(nFilters, nfft, sampleRate, minFrequency = 0,
    maxFrequency = null, scale = MelScale.Htk, areaNormalized = false)`, returning
    `double[][]` with one row per filter.
- **The edges.**
  - `M_lo = hz_to_mel(min)` and `M_hi = hz_to_mel(max)`, in the chosen scale.
  - `m_i = M_lo + (M_hi − M_lo)·i/(n_filters + 1)` for `i = 0 … n_filters + 1`, computed in
    this order in both languages.
  - `f_i = mel_to_hz(m_i)`.
  - `max_frequency` defaults to `fs/2`.
- **The weights.**
  - Bin `k` has frequency `b_k = k·fs/nfft`, for `k = 0 … nfft//2`.
  - Filter `i` (counting from 0) has
    `W[i][k] = max(0, min((b_k − f_i)/(f_{i+1} − f_i), (f_{i+2} − b_k)/(f_{i+2} − f_{i+1})))`.
  - That is a triangle rising from `f_i` to a peak of 1 at `f_{i+1}`, then falling to `f_{i+2}`,
    evaluated at the exact bin frequencies.
- **The normalization.** `area_normalized` multiplies row `i` by `2/(f_{i+2} − f_i)` (Slaney),
  so each triangle has unit area in Hz. The default leaves peaks of 1.
- **Empty filters.** A filter narrower than the bin spacing can catch no bin, and its row is
  all zero. This is allowed and documented, not an error, because it depends only on the
  arguments and the caller can see it.
- **The rules.**
  - `n_filters ≥ 1`.
  - `nfft ≥ 2`.
  - `sample_rate` is finite and positive.
  - `0 ≤ min_frequency < max_frequency ≤ fs/2`, all finite.
  - `scale` is as in ADR 0154.
  - Anything else is `invalid_argument`.

## Consequences

- **Apply it with a matrix product.** `bands = W @ power_spectrum`, for a one-sided spectrum
  of `nfft//2 + 1` bins.
- **Vectors are hand-worked.**
  - On the Slaney scale below 1 kHz, the mel is linear, so the edges are evenly spaced in Hz.
    0 to 1000 Hz in 4 filters gives edges every 200 Hz, and with 100 Hz bins the weights are
    0, ½, 1, ½, 0.
  - The HTK and Slaney log-region cases compute the edges and weights in 50-digit `decimal`
    from the formulas.
  - The cases are:
    - the linear case, with and without area normalization;
    - a non-zero minimum;
    - HTK;
    - the Slaney log region;
    - the default maximum;
    - empty filters;
    - the errors.
- **Tests.**
  - Unnormalized peaks are 1 at a bin that lands on an edge.
  - Adjacent filters sum to 1 between their peaks.
  - Area-normalized rows integrate to about 1 on a fine grid.
