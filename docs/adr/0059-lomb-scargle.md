# ADR 0059: Lomb-Scargle periodogram

Status: accepted, 2026-11-13

## Context

Every spectral estimator in SignalForge assumes evenly spaced samples. Measurements with gaps,
jitter or event-driven timestamps need a periodogram that takes the times as given. The
Lomb-Scargle periodogram (Lomb 1976, Scargle 1982) is the standard one: for each trial frequency
it is the power of the least-squares fit of a sinusoid to the data, and on even samples at a bin
frequency it is the classical periodogram.

## Decision

- `lomb_scargle(times, values, frequencies, *, center=True, normalization="standard")` in
  `signalforge.spectral`; C# `Spectral.LombScargle(times, values, frequencies, center,
  normalization)` with `LombScargleNormalization.Standard` and `.Power`. It returns one value per
  trial frequency, in their order.
- The caller gives the frequencies (Hz, cyclic, finite and positive). There is no automatic grid:
  the right grid depends on the time span and the frequencies of interest, and a default would
  quietly undersample peaks.
- The classic form with Scargle's time offset τ, so the result does not depend on where time zero
  is and equals the least-squares fit. Real values only. A floating fit of the mean ("generalized"
  Lomb-Scargle) and error weights are not included.
- `center` subtracts the mean of the values first, the usual practice; without it, data with a
  nonzero mean show it as power at low frequencies.
- Two normalizations. `"power"` is Scargle's `P`, in value units squared, which is `A²N/4` for a
  sinusoid of amplitude `A` at a bin of `N` even samples. `"standard"` is `2P/Σy²`, the fraction of
  the (centered) data's sum of squares that the sinusoid explains, between 0 and 1. It is the
  default because it reads the same for any data scale.
- A sum `Σsin²` or `Σcos²` below `1e-12·N` (such as `Σsin²` at Nyquist of even samples) makes its
  term 0 rather than a ratio of two rounding errors.

## Consequences

- The expected values come from an independent route: solving the two-parameter least-squares
  fit directly (`P = (Σy² − χ²_min)/2`) with no τ, plus closed forms for even sampling.
- False-alarm probabilities, the generalized form, and a frequency-grid helper can be added later
  without changing this function.
