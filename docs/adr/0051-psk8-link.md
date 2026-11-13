# ADR 0051: 8-PSK in the link

Status: accepted, 2026-11-13

## Context

ADR 0050 added the link's `modulation` field with QPSK and 16-QAM, which share the fourth-power
block phases. 8-PSK's fourth power is ±1, so it needs the eighth power; `power_frequency_offset`
(ADR 0049) already gives the coarse frequency at power 8.

## Decision

- `psk8_phase_offset` and `psk8_block_phases`: the QPSK estimators with `z⁸` (8-PSK's points are
  at multiples of π/4, so `E[s⁸] = 1`) and a π/4 ambiguity. Separate names rather than a power
  argument on the QPSK functions, matching `qpsk_*`, `psk8_*` and `qam16_*` elsewhere.
- `"psk8"` is a third value of `modulation`: coarse frequency at power 8, eighth-power block
  phases, the preamble rounding to multiples of π/4, then the 8-PSK loop, demapper and theory.

## Consequences

- The block phases must move by less than π/8 per block, half QPSK's margin: the coarse
  frequency must be within `Rs/(16·B)` (about 2 Hz at 1000 Bd and 32-symbol blocks), which
  `power_frequency_offset` meets over a whole frame.
- The eighth power raises noise more than the fourth, so the block phases are noisier at the
  same Es/N0; 8-PSK runs at a higher Eb/N0 than QPSK for the same BER anyway.
