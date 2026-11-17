# ADR 0232: CIC droop compensator

Status: accepted, 2026-11-17. It follows ADR 0229 (CIC decimator) and ADR 0230 (CIC
interpolator).

## Context

A CIC filter's passband droops like `sinc^N`. The usual fix is a short FIR at the low rate whose
gain is the inverse of that droop up to a cutoff. Users would otherwise have to work out the
droop themselves and feed it to `fir_frequency_sampling`.

## Decision

- **The API.**
  - Python: `cic_compensator(factor, stages, num_taps, cutoff, sample_rate, *, delay=1)` in `dsp`.
  - C#: `Dsp.CicCompensator(factor, stages, numTaps, cutoff, sampleRate, delay = 1)`.
  - `sample_rate` is the low rate: the decimator's output rate, or the interpolator's input rate.
- **The droop.** At low-rate frequency `f` in cycles per sample,
  `A(f) = |sin(π M f) / (R M sin(π f / R))|^N`, with `A(0) = 1`. This is `|cic_taps|` at the high
  rate frequency `f/R`, divided by the DC gain `(RM)^N`.
- **The design.** It uses frequency sampling with no window and is type 1.
  - `T = num_taps` must be odd, and `c = (T − 1)/2`.
  - The grid is `f_j = j/T` for `j = 0 … c`. The desired gain is `D_j = 1/A(f_j)` where
    `j/T ≤ cutoff/sample_rate`, and 0 elsewhere.
  - The taps are `h[n] = (D_0 + 2 Σ_{j=1}^{c} D_j cos(2π j (n − c)/T)) / T`.
  - The response at each grid frequency is exactly `D_j`. Between grid points it interpolates.
- **The rules.**
  - `factor`, `stages` and `delay` must be integers `≥ 1`, with `stages ≤ 64`.
  - `num_taps` must be an odd integer `≥ 1`.
  - `sample_rate` must be finite and positive.
  - `cutoff` must be finite, with `0 < cutoff ≤ sample_rate/(2M)`. This keeps the passband
    below the first null at `f = 1/M`.
  - Every `D_j` must be finite. A droop so deep that `1/A` overflows is an error.

## Consequences

- **Vectors.** The generator computes `A` from the closed form and the taps from the cosine sum
  in the standard library. It cross-checks two things:
  - `A` against the DTFT of the integer CIC taps;
  - the designed response at each grid frequency against `D_j`.
