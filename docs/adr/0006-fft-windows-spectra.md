# 0006: FFT, windows and spectra

Date: 2026-11-13. Status: accepted.

## Context

Phase 3 needs spectra: a PSD to look at, occupied bandwidth, and channel power. Both languages need
an FFT, a set of windows, and one written definition of each spectral quantity so that the two
implementations agree to rounding error.

Options for the FFT:

| | Python | C# |
|---|---|---|
| Library | `numpy.fft` (pocketfft, BSD-3, already inside NumPy); SciPy's `scipy.fft` | Math.NET Numerics (MIT), FftSharp (MIT) |
| Own | not worth it: NumPy's is already a dependency | iterative radix-2 plus Bluestein for other lengths, ~150 lines |

## Decision

- **Python uses `numpy.fft`.** It is already a dependency, it is fast, it handles every length, and
  its default scaling is our convention. SciPy is not needed for this.
- **C# gets its own FFT**: iterative radix-2 for powers of two, Bluestein's chirp-z algorithm for
  every other length (built on the radix-2 transform). The library stays free of package
  dependencies, the code is small and well understood, and it is tested against a direct DFT and
  closed-form transforms. Math.NET stays the fallback if speed ever matters more than the zero-
  dependency rule; the public API (`Spectral.Fft`, `Spectral.Ifft`) would not change.
- The two FFTs are independent implementations, which is what the shared vectors are for: a
  mistake in one does not hide in the other.
- **Windows are written from their formulas in both languages**, not taken from a library, so the
  definitions (periodic vs symmetric, coefficients) are ours and identical. Periodic is the default,
  because that is the right form for spectral analysis; symmetric is available for filter design.
- **One spectral module per language:** `signalforge.spectral` and the static class
  `SignalForge.Spectral`. It holds the FFT, frequency axes, windows, Welch PSD, occupied bandwidth
  and channel power. Spectral *measurements* (OBW, channel power) live here rather than in
  `measurements` because they work on a PSD, not on samples.
- Definitions are in [conventions.md](../conventions.md) → Spectra. Summary:
  - PSD by Welch's method, normalized by `fs·Σw²` so the PSD integrates to mean power.
  - Complex input gives a two-sided, centered PSD; real input gives a one-sided PSD by default.
  - Occupied bandwidth: the ITU-R SM.328 β/2 method, with each PSD bin treated as a rectangle so
    the band edges are interpolated within a bin.
  - Channel power: the PSD integrated over a frequency range, with partial bins counted pro rata.

Not decided yet (comes with need): zero-padding, detrending, median averaging, spectrograms, an
amplitude-calibrated "power spectrum" view for tone levels. Each is added to conventions.md before
it is coded.
