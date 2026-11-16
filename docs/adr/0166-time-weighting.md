# ADR 0166: Time weighting

Status: accepted, 2026-11-16. With the weighting filters (ADR 0165), it makes a sound level
meter.

## Context

A sound level meter smooths the squared, frequency-weighted signal with an exponential time
weighting. IEC 61672-1 defines it as an analog first-order low-pass with time constant `τ`:
Fast is `0.125` s and Slow is `1` s. Digital versions differ on four points:

- the coefficient: the exact `exp(−1/(τ fs))`, or the Euler `1 − 1/(τ fs)`;
- the initial state;
- whether the output is power or dB;
- whether there is one output per sample or a decimated output.

## Decision

- **The API.** In `measurements`:
  - Python: `time_weighting(samples, sample_rate, time_constant)`.
  - C#: `Measurements.TimeWeighting(samples, sampleRate, timeConstant)`, for real and complex
    samples, returning `double[]`.
- **The recurrence.** `y[n] = α·y[n−1] + (1 − α)·|x[n]|²`, with `y[−1] = 0`.
  - `α = exp(−1/(τ·fs))`. This is the exact discretization of the analog response for an
    input held over each sample.
  - `1 − α` is computed as `−expm1(−1/(τ·fs))`, so that a large `τ·fs` keeps its digits.
- **The output.** One value per input sample, as a power in the units of `|x|²`. The caller
  converts it to dB with `lin_to_db`, against whatever reference they choose.
- **The equivalent level.** `L_eq` is the mean of `|x|²`, which `power_stats` already gives as
  `mean_power`. No new function is needed.
- **The rules.**
  - The samples are real or complex, one-dimensional and finite. An empty input gives an
    empty output.
  - `sample_rate` and `time_constant` are finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **The output starts at 0 and rises.** A meter usually skips the first few `τ`.
- **Vectors come from the closed form.** They use
  `y[n] = (1 − α)·Σ_{k ≤ n} α^(n−k)·|x[k]|²`, in 50-digit `decimal`. The cases are:
  - a unit step at `τ·fs = 1`, which gives `1 − e^(−(n+1))`;
  - Fast and Slow at 48 kHz;
  - complex samples;
  - the empty input;
  - the errors.
