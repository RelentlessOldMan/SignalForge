# ADR 0043: Gardner timing recovery

Status: accepted, 2026-11-13

## Context

`timing_offset` estimates one offset for a whole block. A receiver whose clock differs from the
transmitter's needs a loop that follows the timing as it moves. The usual parts are a timing
error detector, a loop filter, and an interpolator that reads the samples between grid points.
Each part has variants, and the loop's state update has several equivalent-looking forms that
give different numbers.

## Decision

- Detector: Gardner's, `Re{conj(z_mid)·(z_k − z_{k−1})}`, which needs no decisions and works at
  two or more samples per symbol. The midpoint is halfway between the two symbol positions
  actually used, not half a nominal symbol back.
- Loop filter: proportional plus integral, acting on the step to the next symbol, which is held
  within half a symbol of nominal so a wild error cannot stop or reverse the loop.
- Interpolator: the `fractional_delay` kernel (Kaiser sinc, `half_width = 8` by default), so the
  loop and the channel model read between samples the same way.
- Gains are given directly (`kp`, `ki`); `pi_loop_gains` turns a bandwidth, a damping factor and
  the detector's slope into them with the standard second-order formulas. The slope depends on
  the pulse and the signal level, so the caller measures or derives it; the tests measure it
  with the loop open (`kp = ki = 0`).
- The result is a record of the symbols, where they were taken, and the detector output, so a
  test can follow the loop.

## Consequences

- Vectors come from a stdlib generator that runs the same recurrence with its own kernel and I0
  series. The loop is contracting, so last-bit differences between math libraries stay small.
- Carrier tracking loops can reuse `pi_loop_gains`.
