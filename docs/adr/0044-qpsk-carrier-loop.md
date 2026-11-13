# ADR 0044: QPSK carrier tracking loop

Status: accepted, 2026-11-13

## Context

`qpsk_phase_offset` and `qpsk_block_phases` estimate the carrier phase over blocks. A residual
frequency offset or phase noise makes the phase move within a block, so a receiver needs a loop
that follows it symbol by symbol. The usual choices for QPSK are a fourth-power detector or a
decision-directed one, run on the symbols after timing recovery.

## Decision

- `qpsk_carrier_tracking(symbols, kp, ki, *, phase=0.0)`: decision-directed, `Im{conj(d)·r}`
  with `d` the nearest constellation point of the corrected symbol `r` (written with signs, not
  a slicer, so both languages decide ties the same way). At good SNR it has less self-noise than
  the fourth-power detector and the same π/2 ambiguity.
- Loop filter: the same proportional-plus-integral form and `pi_loop_gains` as the timing loop.
  The integrator converges to the frequency offset in radians per symbol.
- The phase is not wrapped, so a test can follow it against an unwrapped truth.
- The result is a record of the corrected symbols, the phase used for each and the detector
  output.

## Consequences

- The π/2 ambiguity and cycle slips are the caller's: a preamble or differential coding
  resolves them.
- Vectors come from a stdlib generator running the same recurrence.
