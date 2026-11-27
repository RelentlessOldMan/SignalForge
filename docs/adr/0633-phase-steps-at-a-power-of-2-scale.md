# ADR 0633: Phase steps at a power-of-2 scale, and the analytic signal scaled down first

Status: accepted, 2026-11-26. Amends ADRs 0123, 0185 and 0187.

## Context

Kay's frequency estimator and the instantaneous frequency take the angle of
`x[n+1]·conj x[n]`. The angle does not change when either sample is scaled, but the product
does: near 2^1000 it overflowed and Kay's estimate was NaN, and near 2^−1000 it underflowed
to 0, so every step was 0 and so was the frequency. A record whose samples differ in size by
2^2000, which no single scale can bring into range, failed too. The analytic signal's FFT
overflowed for a record near the top of the range (a 16-sample sine times 2^1020 has a
bin-3 term of 2^1023, which the weight 2 doubles), although the analytic signal itself was
in range. Both languages had all three faults. The previous probes passed only real arrays
to the measurement module, and the complex probe and the probe of the other modules found
these.

## Decision

- Kay's estimator and the instantaneous frequency multiply each sample by the power of 2 that
  brings its larger real or imaginary magnitude into [1, 2), zeros unchanged, before forming
  each product. Each sample is scaled on its own, because an angle ignores the size of each
  factor; this covers records of any dynamic range.
- The analytic signal scales the record down by the power of 2 that brings its largest
  magnitude into [1, 2) when that magnitude is 2 or more, takes the FFT and its inverse, and
  scales the result back. The analytic signal is linear, so the result is the same. It does
  not scale small records up: their analytic signal is just as small, and scaling up would
  change only the last bits of subnormal intermediates, which no vector can pin.

The scaling is exact. Results that did not overflow or underflow before are unchanged, bit for
bit.

## Consequences

- An analytic signal that is itself out of range still overflows.
- New vectors: `analytic_signal.huge`; `instantaneous_frequency.huge` and `.tiny` (cos_even
  times 2^±1000); `kay_frequency.huge` and `.tiny` (a 64-sample tone of amplitude 2^±1000);
  and `kay_frequency.mixed_scales`, steps of π/2 between samples of size 2^1000 and 2^−1000,
  which one common scale cannot fix. All 6 failed in both languages before the change. An
  axis-aligned Kay case times 2^1000 passed even before the change, since `atan2(inf, 0)` is
  still π/2, so the tone is used instead.
- Mutation checks, in each language: not scaling the analytic signal failed `analytic_signal.huge`.
  Capping the per-sample exponent at 0 from above failed the two `huge` cases, and capping it
  from below failed the two `tiny` cases and `mixed_scales`.
