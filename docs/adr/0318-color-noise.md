# ADR 0318: Colored noise

Status: accepted, 2026-11-18.

## Context

Pink, brown and blue noise are white noise with a power spectrum tilted as `1/f^α`: pink
(`α = 1`) has equal power per octave, brown (`α = 2`) is integrated white noise, and blue
(`α = −1`) rises with frequency. They are used as test signals for audio, for flicker noise in
oscillators, and as backgrounds for detectors.

The random streams differ between the languages, so a generator that draws its own noise could
only be checked by statistics. Shaping white samples the caller passes in is deterministic,
so the shaping itself can be checked sample for sample. The caller draws the white samples
with either language's generator.

## Decision

- **The API.**
  - Python: `color_noise(white, exponent)` in `channel`.
  - C#: `Channel.ColorNoise(ReadOnlySpan<double> white, double exponent)`.
  - Real input and output, the same length.
- **The value.**
  - `N = len(white)`, `X = DFT(white)`.
  - Bin `k` of the full DFT is scaled by `g_k = m^(−α/2)`, where `m = min(k, N − k)`. Bin 0 is
    set to 0: `1/f^α` has no finite value at DC for `α > 0`, and a mean in the white samples
    would otherwise dominate.
  - `g_k = g_(N−k)`, so the spectrum stays Hermitian and the output is real:
    `y = Re(IDFT(g·X))`.
  - The power of bin `k` is scaled by exactly `m^(−α)`.
  - The output is not normalized. For `α = 0` it is the white samples less their mean.
  - The shaping is circular: the output wraps round, as one period of a periodic noise.
- **The rules.**
  - `white` real, one-dimensional and finite; it may be empty, and `N = 1` gives `[0]`.
  - `exponent` finite.

## Consequences

- **Vectors.**
  - `g` is real and even, so the shaping is the circular convolution of `white` with
    `h[j] = (1/N)·Σ_k g_k·cos(2π·k·j/N)`.
  - The generator computes `h` and the convolution directly, with `math.cos` and
    `math.fsum`, without an FFT.
  - It checks that `α = 0` gives the white samples less their mean.
  - The tolerance is `abs 1e-12, rel 1e-12`.
