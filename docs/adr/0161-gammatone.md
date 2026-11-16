# ADR 0161: Gammatone impulse response

Status: accepted, 2026-11-16. It uses the ERB bandwidth (ADR 0160).

## Context

The gammatone filter models the cochlea's auditory filter. Its impulse response is

`g(t) = t^(N−1)·exp(−2π·b·ERB(f_c)·t)·cos(2π f_c t)`,

where `N = 4` and `b = 1.019` are the usual values (Patterson et al.). Implementations differ
on three points:

- the gain normalization;
- the phase;
- whether they sample the impulse response (an FIR) or use a recursive approximation.

## Decision

- **The API.** It is a sampled FIR, so it works with `convolve` and `FirFilter`.
  - Python: `gammatone(center_frequency, sample_rate, length, *, order=4,
    bandwidth_factor=1.019)`, in `dsp`.
  - C#: `Dsp.Gammatone(centerFrequency, sampleRate, length, order = 4,
    bandwidthFactor = 1.019)`, returning `double[]`.
- **The taps.**
  - `h[n] = g(n/fs)/G` for `n = 0 … length − 1`, with cosine phase and `ERB` from
    `erb_bandwidth`.
  - `t^0 = 1` at `t = 0`, so for `N = 1` the first tap is not zero.
- **The normalization.**
  - `G = |Σ_n g(n/fs)·e^(−j ω_c n)|`, with `ω_c = 2π f_c/fs`.
  - The taps therefore have exactly unit gain at `f_c`.
  - If `G` is not positive, the call is an error: the taps would all be 0 or the response
    would cancel. That happens, for example, with one tap when `N ≥ 2`.
- **The rules.**
  - `sample_rate` is finite and positive.
  - `0 < center_frequency < fs/2`.
  - `length ≥ 1`.
  - `order ≥ 1` is an integer.
  - `bandwidth_factor` is finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **Truncation is the caller's choice.** The envelope decays as `exp(−2π b ERB t)`, so a few
  times `1/(b·ERB)` seconds holds nearly all of the energy.
- **The bandwidth.** For `f_c` well above the bandwidth, the −3 dB width is
  `2·√(2^(1/N) − 1)·b·ERB`, which is `≈ 0.887·ERB` for `N = 4` and `b = 1.019`. This is a test,
  not a vector, because the image at `−f_c` shifts it slightly.
- **Vectors come from the closed form.** They are evaluated in 50-digit `decimal`, with π from
  Machin's formula and cos and sin from their Taylor series. The cases are:
  - orders 1, 2 and 4;
  - a non-default bandwidth factor;
  - a single tap;
  - the errors, including a zero response.
