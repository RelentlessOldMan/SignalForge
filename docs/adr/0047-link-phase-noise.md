# ADR 0047: Phase noise in the QPSK link

Status: accepted, 2026-11-13

## Context

The link's fine carrier estimate is one straight line through the block phases, so it removes a
constant frequency and phase but not an oscillator's random wander. `phase_noise` models that
wander and `qpsk_carrier_tracking` follows it; the link should be able to show both.

## Decision

- A config field `phase_noise_linewidth_hz` [0], applied in the channel right after the carrier
  offset (it is the oscillator's), before the clock offset and the noise.
- One generator seeded with `seed` drives the phase noise, then the AWGN. Seeding the two from
  the same integer separately would give them the same normal draws; a derived seed (`seed + 1`)
  would overflow in C# at the top of the range. With no phase noise nothing is drawn for it, so the
  AWGN and every existing report stay the same.

- The carrier loop starts at the preamble's data-aided phase, not at the block line's phase
  (this replaces that point of ADR 0046). The line is fitted over the whole frame, so under phase
  noise its phase at the frame start can be off by more than π/4, and a loop started there locks
  to the wrong quadrant for the whole frame. The preamble phase is local and unambiguous.

## Consequences

- With phase noise the Python and C# streams differ as before; noisy link configs compare by
  statistics.
