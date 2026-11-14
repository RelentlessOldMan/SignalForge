# ADR 0065: Phase noise and clock offset in the OFDM link

Status: accepted, 2026-11-13

## Context

The OFDM link ([ADR 0063](0063-ofdm-link.md), [ADR 0064](0064-link-multipath.md)) rejects phase
noise and a clock offset. Phase noise turns slowly against a block, so its common part is what the
per-block phase already tracks; what is left leaks between subcarriers. A receiver clock that runs
off by `ε` moves the DFT window by `ε·(N + cp)` samples a block against the signal, which shows as a
phase growing linearly across subcarriers, `2πkτ_b/N`, and over a long frame `τ` leaves the prefix.
`clock_offset` also changes the received length.

## Decision

- `phase_noise_linewidth_hz` and `clock_offset_ppm` are accepted for `"ofdm"`, applied in the
  channel as for the other chains.
- The frame is followed by `⌊cp/2⌋` zeros (always, replacing ADR 0064's `max(delays)`), so the
  received signal holds every echo and a slow clock leaves the windows inside it. The total drift
  must fit the margin the back-off leaves: `|clock_offset_ppm|·10⁻⁶·(delay_samples + L) ≤
  ⌊cp/2⌋ − D`, `D` the largest path delay (0 without multipath).
- `timing_loop_gains` `[kp, ki]` turn on, for OFDM, a second-order loop on the window offset `τ`
  in samples, run with the per-block phase. Block by block: derotate by `θ + 2πkτ/N`, decide,
  take the common phase `a` of the residual and `θ ← θ + a`, fit the slope of the residual
  phases against `k` by least squares, `e = (N/2π)·slope`, then `v ← v + ki·e`, `τ ← τ + kp·e +
  v`; the block's output uses the updated `θ` and `τ`. Without gains, `τ` stays 0 and the block
  phase is ADR 0063's. `carrier_loop_gains` stay rejected: the block phase is the carrier loop.
- **Preamble phase alignment** (found in testing: with 200 preamble blocks at 10 dB the
  prefix's frequency estimate was 0.08 Hz off, the phase turned 2.1 rad over the preamble, the
  averaged `Ĥ` started the block phase more than π/4 away and it locked a quadrant off; 0.5 Hz of
  phase noise wanders about 1 rad over 16 blocks the same way): each preamble block's estimate
  `Z/A` is turned to block 0's common phase before the average, and the block loop runs through
  the preamble on the known symbols, so it enters the data with the phase and window offset of
  the last preamble block. A first try fitted a residual frequency to the preamble instead; it
  fixed the offset but not phase noise.
- Clock-offset runs need guard subcarriers: resampling cannot keep a subcarrier at or near
  Nyquist (the default set includes `−N/2`), and in testing that one subcarrier carried most of the
  errors.
- `ber_theory` is unchanged, the known-channel value without phase noise or clock offset: the
  leakage has no closed form here, so the tests bound the loss.

## Consequences

- An OFDM run with a drifting clock decodes when the loop is on and fails when it is off.
- The prefix metric and the preamble estimate do not model the drift; that limits the clock
  offset a frame can carry to the stated margin.
