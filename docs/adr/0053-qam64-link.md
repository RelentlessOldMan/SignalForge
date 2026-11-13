# ADR 0053: 64-QAM carrier loop and link

Status: accepted, 2026-11-13

## Context

ADR 0052 added 64-QAM's mapper, demappers and theory, leaving the carrier loop and the link for
later. The link already handles 16-QAM through fourth-power estimators (ADR 0050).

## Decision

- `qam64_carrier_tracking`, the shared decision-directed PI loop with `d` the point
  `qam64_demap_hard` decides, so the loop and the demapper never disagree on a tie.
- `"qam64"` as a link `modulation`: the 16-QAM chain (fourth-power coarse frequency, block phases
  and π/2 resolution, since `E[s⁴]` is a negative real for 64-QAM too) with 64-QAM's mapper, loop,
  demapper and theory.

## Consequences

- 64-QAM's fourth power has more self-noise than 16-QAM's, so the block phases are noisier: at
  Eb/N0 14 dB, 32-symbol blocks scatter by 0.105 rad and some steps come near π/4, so the
  unwrapping slips by π/2 and the fit fails (BER 0.43 over 20000 symbols). 64-symbol blocks and
  longer work (273–276 bit errors against 258 from theory). The default `phase_block_symbols`
  stays 32 so existing reports do not change; a 64-QAM config sets it, as `qam64_14db` does
  (128).
