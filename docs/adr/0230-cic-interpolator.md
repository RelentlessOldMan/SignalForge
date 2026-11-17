# ADR 0230: CIC interpolator

Status: accepted, 2026-11-17. It is the counterpart of ADR 0229 (the CIC decimator).

## Context

The CIC interpolator is the last stage of a digital up-converter. It runs `N` combs at the low
rate, inserts `R − 1` zeros after each sample, and then runs `N` integrators at the high rate.
It has the same response as the decimator, `cic_taps`, applied at the high rate.

## Decision

- **The API.**
  - Python: `cic_interpolate(samples, factor, stages, *, delay=1)` in `dsp`.
  - C#: `Dsp.CicInterpolate`, with real and complex overloads.
- **The value.**
  - `u` is the zero-stuffed input: `u[k·R] = x[k]`, with the other samples 0.
  - `y[n] = Σ_m h[m]·u[n − m]` for `n = 0 … L·R − 1`, with `h = cic_taps(R, N, M)` and `u` zero
    outside `0 … L·R − 1`. The output is causal and `L·R` samples long, the same length as the
    streaming `Resampler` would give.
  - By the noble identity, this is exactly `N` combs of delay `M` at the low rate, zero-stuffing,
    and then `N` integrators.
  - The output is not normalized. A constant input settles to `(R·M)^N / R`, since each output
    sees one input in `R`.
- **The computation.** It is computed as the polyphase FIR. Output `n` sums `h[m]·x[(n − m)/R]`
  over the `m ≡ n (mod R)` with `0 ≤ n − m`, in increasing `m`. Floating-point integrators would
  grow without bound, as in ADR 0229.
- **The rules.**
  - The same as `cic_decimate`: integers `≥ 1`, `stages ≤ 64` and `(R·M)^N ≤ 2^53`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.** The expected values come from running the comb–zero-stuff–integrator structure in
  exact arithmetic in the generator. They are cross-checked against the FIR form.
