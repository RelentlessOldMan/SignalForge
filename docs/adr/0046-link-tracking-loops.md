# ADR 0046: Tracking loops in the QPSK link

Status: accepted, 2026-11-13

## Context

The link receiver estimates timing, frequency and phase over the whole frame. A sample clock
offset makes the symbol timing drift through the frame, which one timing estimate cannot follow.
`gardner_timing`, `qpsk_carrier_tracking` and `clock_offset` now exist; the link should be able to
use them.

## Decision

- Three config fields, all off by default so existing configs and reports are unchanged:
  `clock_offset_ppm` (channel), `timing_loop_gains` and `carrier_loop_gains` (receiver), each a
  pair `[kp, ki]` or none.
- The config takes loop gains, not a loop bandwidth: the detector gain depends on the pulse and the
  signal level, and a caller who wants a bandwidth computes the gains with `pi_loop_gains`. The
  config stays a plain record of numbers both languages read the same way.
- The timing loop replaces the fixed-phase decimation and starts at the block timing estimate. The
  carrier loop runs after the block frequency and phase correction, from phase 0, so the preamble
  has already resolved the π/2 ambiguity.
- The clock offset is applied after the carrier offset and before the noise: it is the receiver's
  sampling, and the noise is added at the receiver's rate.
- The report's fields keep their meaning; `timing_offset` is the loop's start when it runs.

## Consequences

- A link with a clock offset and the timing loop off loses lock over a long frame; with it on the
  BER comes back to theory.
- Without noise both languages run the same recurrences, so a noiseless tracking config compares
  as tightly as before.
