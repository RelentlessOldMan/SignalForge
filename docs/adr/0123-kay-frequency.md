# ADR 0123: Single-tone frequency estimate (Kay)

Status: accepted, 2026-11-16. It extends the measurements (conventions: Measurements).

## Context

An FFT peak gives a tone's frequency to a bin. Many measurements need it finer: a carrier
offset, a reference oscillator's error, or the frequency to center a tone fit on. Kay's estimator
(S. Kay, "A fast and accurate single frequency estimator", IEEE Trans. ASSP, 1989) works like
this:

- It averages the phase steps between neighbouring samples with parabolic weights.
- It is closed form, with no search or FFT.
- It is exact for a noiseless complex tone.
- At high SNR, it reaches the Cramér-Rao bound.

## Decision

- Python `kay_frequency(samples, sample_rate)` and C# `Measurements.KayFrequency(samples,
  sampleRate)`, for complex samples. Python also takes a real array, read as complex with zero
  imaginary part.
- **The phase steps.** For `n = 0 … N − 2`, `Δ_n = atan2(Im z_n, Re z_n)`, where
  `z_n = x[n+1]·conj(x[n])`. This is written out as `(ac + bd) + i(bc − ad)` for
  `x[n+1] = a + ib` and `x[n] = c + id`.
- **The weights.** `w_n = (3N / (2(N² − 1)))·(1 − ((n − (N/2 − 1)) / (N/2))²)`, with real
  division. They sum to 1.
- **The result.** `f = sample_rate·Σ w_n Δ_n / (2π)` in Hz, in `(−fs/2, fs/2]`.
- **The rules.**
  - At least two samples are needed.
  - Every sample must be finite and **non-zero**.
  - `sample_rate` must be finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **Zero samples.** A zero sample has no phase, and `atan2` of a signed zero is `0` or `π`
  depending on the sign bits. Two libraries could then disagree by half the sample rate, so zero
  samples are an error instead.
- **Ambiguity.** For a noiseless tone, every `Δ_n` is the same wrapped step, so `f` is exact
  for any `|f| < fs/2`. Near `±fs/2`, noise wraps the steps and the estimate breaks down. This is
  the estimator's known limit, documented here and not guarded.
- **Real input.** A real tone holds two complex tones at `±f`. Kay's estimator is meant for
  complex (analytic or I/Q) samples, so a real input gives a meaningless answer.
- **Vectors.** These are worked by hand:
  - `[1, i, −1, −i]` steps by `π/2`.
  - Mixed steps: `[1, 1, i]` has weights `½, ½`, and `[1, i, i, i, −1]` has weights
    `0.2, 0.3, 0.3, 0.2`.
  - A negative frequency.
  - Noiseless tones whose expected value is the frequency they were made with.
  - The errors.
- **Tests.**
  - Noiseless tones over a sweep of frequencies are exact.
  - At 30 dB SNR, the variance is within 15 % of the CRLB `6/((2π)²·SNR·N(N² − 1))`, in
    cycles per sample squared.
  - Amplitude and starting phase change nothing.
