# ADR 0132: Spectral irregularity

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

Spectral irregularity measures how jagged a PSD is from bin to bin. Jensen's form is
`Σ (P_k − P_{k+1})² / Σ P_k²` over the bins' powers. It counts bins, so an edge piece cut down
to a sliver would still count a full jump.

## Decision

- **The API.**
  - Python: `spectral_irregularity(frequencies, psd, *, band=None, span=None)`, returning a
    float.
  - C#: `Spectral.SpectralIrregularity(frequencies, psd, band, span)`.
- **The pieces.** The PSD is a step density on the pieces `[a_k, b_k]` of the spectral moments,
  with density `d_k` and width `w_k`.
- **The jumps.** Each jump between neighbouring pieces is weighted by the mean width of the two
  pieces, so a sliver counts for little.
- **The value.** `irregularity = Σ_k (d_k − d_{k+1})² (w_k + w_{k+1})/2 / Σ_k d_k² w_k`. It is
  dimensionless.
- **Uncut bins.** When no bin is cut, every weight is the bin spacing, so this is exactly
  Jensen's form.
- **The rules.**
  - The band rules are those of spectral flatness.
  - The band needs at least two pieces and positive power.
  - Anything else is `invalid_argument`.

## Consequences

- **What it means.** A flat PSD gives 0. Reversing the PSD changes nothing.
- **Vectors.** These are worked by hand with Fractions:
  - flat: 0.
  - ramp: 1/10.
  - alternating: 3/2.
  - a single bin: 2.
  - a cut band and the span.
  - the errors.
- **Tests.**
  - Scaling the PSD changes nothing.
  - Stretching the axis changes nothing.
  - Reversing the PSD changes nothing.
  - Uncut bins match Jensen's form computed directly.
