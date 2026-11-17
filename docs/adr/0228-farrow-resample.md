# ADR 0228: Farrow resampler

Status: accepted, 2026-11-17. It builds on ADR 0226 (the Farrow variable delay).

## Context

`resample` (ADR 0035) converts between rates whose ratio is a small fraction `up/down`. Ratios
such as 44 100 → 48 000 with a drifting clock, or any irrational ratio, need an interpolator
read at arbitrary positions. ADR 0226's Farrow structure does that cheaply: one set of fixed
sub-filters and a Horner evaluation per output sample.

## Decision

- **The API.**
  - Python: `farrow_resample(samples, ratio, *, order=3)` in `channel`, beside `farrow_delay`.
  - C#: `Channel.FarrowResample(samples, ratio, order = 3)`.
  - The output is complex.
- **The value.**
  - `ratio` is the output rate over the input rate.
  - Output `k` reads the input at `t_k = k / ratio`, computed as one floating-point division,
    for `k = 0, 1, …` while `t_k ≤ L − 1`.
  - Each read is ADR 0226's interpolator at position `t_k`: `q = t_k − (N−1)/2`, `b = ⌊q⌋`,
    `μ = q − b`, with the same Farrow evaluation and `x` zero outside `0 … L−1`.
  - So `farrow_resample` reads at `k/ratio` and `farrow_delay` reads at `n − delays[n]`. The two
    share one implementation in each language.
  - With an odd order and `ratio = 1/M` for an integer `M`, every read is on a sample, and the
    result is exact decimation by `M`.
- **No anti-aliasing.** There is no anti-alias filtering. Decimating a signal with content above
  the new Nyquist frequency aliases it, as with `clock_offset`. Low-pass first, for example with
  `resample` or an FIR.
- **The rules.**
  - `ratio` must be finite and within `[1e-6, 1e6]`. This bounds the output length.
  - `order` must be an integer `≥ 1`.
  - Empty input gives empty output.

## Consequences

- **Vectors.**
  - The expected values come from exact rational arithmetic in the generator, with the Lagrange
    product form.
  - The read positions are the generator's own floating-point `k / ratio`, as the convention
    defines them, taken exactly.
  - Polynomial inputs are checked to come out as the polynomial at `t_k` wherever all `N + 1`
    samples are inside.
