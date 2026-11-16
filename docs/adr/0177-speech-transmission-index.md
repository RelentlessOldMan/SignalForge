# ADR 0177: Speech transmission index from an MTF matrix

Status: accepted, 2026-11-16. It builds on the modulation transfer function (ADR 0176).

## Context

The speech transmission index (STI) of IEC 60268-16 combines the modulation transfer of 7
octave bands, 125 Hz to 8 kHz, at 14 modulation frequencies, 0.63 Hz to 12.5 Hz in third
octaves. The full procedure also corrects each `m` for:

- the speech level;
- auditory masking from the band below;
- the absolute hearing threshold.

Those corrections need band levels and tables of their own.

## Decision

- **The API.** In `measurements`:
  - Python: `speech_transmission_index(mtf)`.
  - C#: `Measurements.SpeechTransmissionIndex(double[][] mtf)`.
  - `mtf` has 7 rows, one per octave band from 125 Hz up, and `M ≥ 1` columns.
  - The full method uses 14 columns, and STIPA's two modulations per band also fit.
  - Every row has the same length.
- **The steps.** These follow IEC 60268-16:2020 (edition 5), Annex A:
  - `SNR = 10·log10(m/(1 − m))`, clipped to `[−15, +15]` dB.
  - `TI = (SNR + 15)/30`. Values of `m ≤ 0` give `TI = 0`, and `m ≥ 1` gives `TI = 1`, which
    are the limits of the clipped formula.
  - `MTI_k` is the mean of the band's `M` TIs.
  - `STI = Σ_{k=1}^{7} α_k·MTI_k − Σ_{k=1}^{6} β_k·√(MTI_k·MTI_{k+1})`.
- **The weights.** They are the male weights of Table A.1 of that edition:
  - `α = 0.085, 0.127, 0.230, 0.233, 0.309, 0.224, 0.173`
  - `β = 0.085, 0.078, 0.065, 0.011, 0.047, 0.095`
  - They were checked against two independent published restatements of the 2020 edition: a
    vendor's compliance example and a national institute's benchmark procedure. Both list the
    same numbers.
  - `Σα − Σβ = 1.381 − 0.381 = 1`, so an STI of 1 needs every `m ≥ 1`.
- **Not included.** The level-dependent masking, the hearing threshold, the ambient-noise
  correction and the female weights.
  - The caller applies any `m` corrections before calling.
  - A later slice may add the female weights, or the masking from band levels.
- **The rules.**
  - `mtf` is two-dimensional, with 7 rows and at least 1 column.
  - Every value is finite.
  - Anything else is `invalid_argument`.
  - Values outside `[0, 1]` are allowed, and clip as above.

## Consequences

- **The result is not the full IEC STI.** It is the STI of the given (already corrected) MTF.
  The docs say so.
- **Vectors are hand values.** They are derived from the formula and the weights in 50-digit
  `decimal`:
  - a uniform `m` gives STI equal to its TI exactly;
  - bands at `m = 1` and `m = 0` give exact sums of the weights;
  - other cases cover clipping, mixed columns and an STIPA-shaped `7 × 2` matrix.
