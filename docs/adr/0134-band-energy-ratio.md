# ADR 0134: Band energy ratio

Status: accepted, 2026-11-16. It extends the spectra (conventions: Spectra).

## Context

The band energy ratio is the power above a split frequency over the power below it. In audio it
tells voiced speech from unvoiced speech and bright sounds from dull ones. In RF it is a quick
tilt check. Libraries sum the bins on each side of the split's bin. That puts the whole of the
straddling bin on one side.

## Decision

- **The API.**
  - Python: `band_energy_ratio(frequencies, psd, split, *, band=None, span=None)`, returning
    `BandEnergyRatio(low, high, ratio, ratio_db)`.
  - C#: `Spectral.BandEnergyRatio(frequencies, psd, split, band, span)`, returning the record
    `BandEnergyRatio(Low, High, Ratio, RatioDb)`.
- **The powers.** The PSD is a step density on the band's pieces, as for the spectral moments.
  - `low = ∫_{low edge}^{split} d df`.
  - `high = ∫_{split}^{high edge} d df`.
  - A bin that straddles the split is shared by width.
- **The ratio.** `ratio = high / low` and `ratio_db = 10 log10(ratio)`.
  - When `low` is 0, these are +∞.
  - When `high` is 0, `ratio` is 0 and `ratio_db` is −∞.
- **The rules.**
  - `split` must be finite and strictly inside the band.
  - The band rules are those of spectral flatness.
  - The band needs positive power.
  - Anything else is `invalid_argument`.

## Consequences

- **Units.** `low` and `high` are powers, in the same units as `channel_power`, and they add up
  to the band's power. The ratio is dimensionless.
- **Vectors.** The powers are worked by hand with Fractions; only the dB is not rational:
  - flat.
  - a ramp split between bins.
  - a ramp split inside a bin.
  - a cut band.
  - the span.
  - no power below the split, and none above, whose infinities are written `"inf"` and
    `"-inf"` (vectors/README.md).
  - the errors.
- **Tests.**
  - `low + high` equals the channel power over the band.
  - Mirroring the PSD about the split inverts the ratio.
  - The two infinite cases.
