# ADR 0104: Sample clock jitter

Status: accepted, 2026-11-16. Extends [ADR 0045](0045-clock-offset.md), which left jitter for
later.

## Context

A real sampling clock has an average rate, and its edges also wander from one sample to the
next. On a tone at `f` that wander becomes phase noise proportional to `f`. That is why jitter
sets the SNR ceiling of a fast converter. A test needs a channel that samples at slightly wrong
instants.

## Decision

- Python `clock_jitter(samples, rms, *, seed, half_width=16)`. C#
  `Channel.ClockJitter(samples, rms, seed, halfWidth = 16)`, with an `int` seed or a `Random`,
  as for phase noise.
- White jitter only: `y[n] = z(n + σ·gₙ)` for `n = 0 … N − 1`, with `σ = rms` in samples.
  - The `gₙ` are independent standard Gaussians, one per sample, drawn in order. Python uses
    `standard_normal(N)` from its generator. C# uses the Box–Muller cosine branch, as for phase
    noise.
  - `z` is the fractional delay read of ADR 0045, with `x` zero outside `0 … N − 1`. A read
    near an end therefore loses part of its kernel, as `fractional_delay` does. The output is as
    long as the input.
  - A random walk of the clock phase (accumulating jitter) is a different model, and it is not
    included.
- `rms` is finite, with `0 ≤ rms ≤ 0.5`. Beyond half a sample the readings reorder, and the call
  stops being a clock error. `half_width` is an integer `≥ 1`. The seed rules are those of AWGN:
  the random streams differ between languages.
- With `rms = 0`, every position is `n + 0·gₙ = n` exactly. So the output is the input, and the
  draws are still taken.

## Consequences

- The only cross-language vectors are seed-independent: `rms = 0`, the empty input, and
  rejected arguments.
- The tests in both languages check statistics against the classic jitter result. For a tone
  `e^{j2πfn}`, the error `y − x ≈ e^{j2πfn}(e^{j2πfσg} − 1)` has mean power
  `2(1 − e^{−(2πfσ)²/2})`, from the Gaussian characteristic function `E e^{jag} = e^{−a²/2}`.
  That is `≈ (2πfσ)²` for small `σ`. The kernel's error floor (about `2·10⁻⁵`) is far below it.
