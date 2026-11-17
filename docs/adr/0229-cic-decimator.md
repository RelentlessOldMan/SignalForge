# ADR 0229: CIC decimator

Status: accepted, 2026-11-17.

## Context

The cascaded integrator-comb (CIC) filter (Hogenauer, 1981) is the standard first decimation
stage after a fast ADC or a digital down-converter. It needs no multiplies. Its response is a
power of a moving sum, and its passband droop is usually corrected by a later FIR. SignalForge
can resample (ADR 0011) with any FIR, but it has no CIC response and no CIC structure.

## Decision

- **The API.**
  - Python: `cic_taps(factor, stages, *, delay=1)` and `cic_decimate(samples, factor, stages, *,
    delay=1)` in `dsp`.
  - C#: `Dsp.CicTaps` and `Dsp.CicDecimate`, with real and complex sample overloads.
- **The taps.** With `R = factor`, `N = stages` and `M = delay`, `h` is the `N`-fold convolution of
  `R·M` ones.
  - It has `N(R·M − 1) + 1` taps, which are the coefficients of `((1 − z^(−RM))/(1 − z^(−1)))^N`.
  - Their sum, the DC gain, is `(R·M)^N`. The taps are not normalized, as in hardware. Divide by
    the gain for unit DC gain.
- **The output.** `y[k] = Σ_m h[m]·x[k·R − m]` for `k = 0 … ⌈L/R⌉ − 1`, with `x` zero before 0.
  - The output is causal, like the streaming `Resampler` (ADR 0027), and starts with the first
    input sample.
  - It is exactly what `N` integrators, keeping every `R`-th sample from `n = 0`, and then `N`
    combs of delay `M` at the low rate produce. That follows from the noble identity.
- **The computation.** The output is computed as the equivalent FIR, not with integrators.
  - Floating-point integrators grow without bound on any signal with a DC part. Hardware relies
    on modular wraparound, which floating point lacks.
  - The FIR form has no growth. For integer input it is exact while `(R·M)^N ≤ 2^53`.
- **The rules.**
  - `factor`, `stages` and `delay` must be integers `≥ 1`, with `stages ≤ 64` and
    `(R·M)^N ≤ 2^53`. Every tap and every partial sum of integer data is then an exact double.
  - The samples must be finite and non-empty, as for `resample`.

## Consequences

- **Vectors.**
  - The taps come from expanding the polynomial with Python integers, and they are checked to sum
    to `(R·M)^N`.
  - The decimator's expected outputs come from running the integrator–decimate–comb structure in
    exact integer or rational arithmetic. They are cross-checked against the FIR form.
- **Not covered.** CIC interpolators and droop-compensation FIRs are not built yet.
