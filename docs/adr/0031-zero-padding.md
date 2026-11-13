# ADR 0031: Zero padding in Welch's method

Status: accepted, 2026-11-13

## Context

Transforming each segment at a length `nfft` above `nperseg` samples the same windowed spectrum
on a finer grid. It adds no resolution, but it locates peaks better and gives plots a smoother
curve. The choices that two implementations could make differently: where the zeros go, whether
the density scale changes with `nfft`, and what `bin_width` and `enbw_hz` mean afterwards.

## Decision

- **`nfft=None`** (meaning `nperseg`) on `welch_psd` and `spectrogram`, `nfft ≥ nperseg`, zeros
  appended after the windowed segment.
- **The scale stays `1/(fs·Σw²)`**, independent of `nfft`. By Parseval at length `M`, the sum of
  the PSD times `fs/M` is still the windowed segments' mean power, so channel power and the
  measurements that multiply by `bin_width` keep their meaning.
- **`bin_width = fs/nfft`** (the spacing of the bins, which the bins-as-rectangles rule needs) and
  **`enbw_hz = ENBW·fs/nperseg`** (the resolution, which padding does not change). Both results
  gain an `nfft` field; C#'s records gain `Nfft` as the last positional member.
- One-sided folding, the shifted order and the frequency axis follow the transform length.

## Consequences

- A padded PSD's bins are correlated, so a bin is no longer an independent noise sample; the
  median bias correction (ADR 0030) assumes nothing about bins and is unaffected.
- C# code that constructed `SpectralDensity` or `Spectrogram` positionally must pass `Nfft`; the
  library is the only place that constructs them.
- Expected values: the stdlib generator sums the DFT over the `nperseg` real samples at frequency
  spacing `fs/nfft`, plus a hand case.
