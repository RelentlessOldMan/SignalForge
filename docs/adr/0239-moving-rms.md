# ADR 0239: Moving RMS

Status: accepted, 2026-11-17.

## Context

A level meter, a VAD, or a gate needs the RMS of the most recent `N` samples at every sample.
The envelope follower (ADR 0238) is a peak detector; this is the true power average over a
rectangular window.

## Decision

- **The API.**
  - Python: `moving_rms(samples, length)` in `dsp`.
  - C#: `Dsp.MovingRms(samples, length)`, for real or complex samples.
  - Both return real values.
- **The value.**
  - `y[n] = sqrt((1/N)·Σ_{k=n−N+1}^{n} |x[k]|²)`, with `N = length` and `x` zero before 0.
  - The window starts from rest, so the first `N − 1` outputs still divide by `N`.
- **The computation.**
  - Each output is summed directly, oldest sample first, at a cost of `O(L·N)`.
  - A running sum would drift and would round differently in each language. Exactness matters
    more here than the cost.
- **The rules.**
  - `length` must be an integer `≥ 1`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.** The expected values are the exact rational mean of the squares, followed by a
  square root in the generator. A constant `a` gives `|a|·sqrt(min(n + 1, N)/N)`.
